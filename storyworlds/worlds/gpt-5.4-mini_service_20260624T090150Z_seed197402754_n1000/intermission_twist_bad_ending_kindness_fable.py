#!/usr/bin/env python3
"""
storyworlds/worlds/intermission_twist_bad_ending_kindness_fable.py
=================================================================

A small fable-style story world built around an intermission, a twist, kindness,
and a bad ending.

Seed tale inspiration:
---
A little forest stage held a tiny play for the animals. At intermission, the
mouse wanted to keep her sweet bun, but the wind blew the curtain loose and a
younger animal needed help. She chose kindness, and the story turned in a way
that felt both surprising and a little sad. In the end, she did the right thing,
but she did not get the reward she hoped for.

World model:
---
- Characters have meters (physical) and memes (emotional).
- The intermission is a real state change: the show pauses, a choice appears,
  and the twist changes what can happen next.
- Kindness can help another character, but in this fable it may cost the hero
  the prize they wanted.
- The ending is intentionally a "bad ending" in the sense that the hero does not
  get the prize; the moral comes from the choice, not the reward.

This script supports:
- default run, -n, --all, --seed, --trace, --qa, --json
- --asp, --verify, --show-asp
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
    kind: str = "character"
    type: str = "animal"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "rabbit", "hare", "squirrel", "badger", "fox", "mole"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little forest stage"
    affords: set[str] = field(default_factory=lambda: {"intermission"})


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    value: str
    risk: str
    at_intermission: bool = True


@dataclass
class HelpNeed:
    id: str
    label: str
    request: str
    fix: str
    consequence: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.intermission = False
        self.twist = False
        self.helped = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.intermission = self.intermission
        clone.twist = self.twist
        clone.helped = self.helped
        return clone


HEROES = [
    ("Milo", "mouse"),
    ("Pip", "rabbit"),
    ("Nina", "squirrel"),
    ("Tib", "hedgehog"),
]

HELPERS = [
    ("Otis", "owl"),
    ("Mira", "mole"),
    ("Bram", "badger"),
]

PRIZES = {
    "seedcake": Prize(
        label="seed cake",
        phrase="a sweet seed cake with honey glaze",
        type="cake",
        value="sweet",
        risk="stolen",
    ),
    "bluebell": Prize(
        label="blue ribbon",
        phrase="a bright blue ribbon for the best listener",
        type="ribbon",
        value="bright",
        risk="lost",
    ),
    "lantern": Prize(
        label="paper lantern",
        phrase="a tiny paper lantern painted with stars",
        type="lantern",
        value="glowing",
        risk="crumpled",
    ),
}

NEEDS = {
    "stuck_curtain": HelpNeed(
        id="stuck_curtain",
        label="stuck curtain",
        request="the curtain rope was caught on a nail",
        fix="pull the rope free",
        consequence="the stage could open again",
    ),
    "spilled_water": HelpNeed(
        id="spilled_water",
        label="spilled water",
        request="a puddle had formed near the front bench",
        fix="wipe up the puddle with a clean cloth",
        consequence="nobody would slip on the floor",
    ),
    "lost_child": HelpNeed(
        id="lost_child",
        label="lost child",
        request="a tiny field mouse had wandered away from the crowd",
        fix="walk the child back to the nest path",
        consequence="the child would not cry alone",
    ),
}

TRAITS = ["gentle", "curious", "quiet", "brave", "patient"]


@dataclass
class StoryParams:
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    prize: str
    need: str
    trait: str
    seed: Optional[int] = None


def _safefirst(words: list[str], rng: random.Random) -> str:
    return rng.choice(words)


def prize_at_risk(prize: Prize, need: HelpNeed) -> bool:
    return True if prize.at_intermission else False


def select_help(prize: Prize, need: HelpNeed) -> bool:
    return prize_at_risk(prize, need)


def valid_combos() -> list[tuple[str, str]]:
    return [(p, n) for p in PRIZES for n in NEEDS if select_help(PRIZES[p], NEEDS[n])]


ASP_RULES = r"""
prize_at_risk(P,N) :- prize(P), need(N).
compatible(P,N) :- prize_at_risk(P,N), helpable(N).
valid(P,N) :- compatible(P,N).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for nid in NEEDS:
        lines.append(asp.fact("need", nid))
        lines.append(asp.fact("helpable", nid))
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable world of an intermission, a twist, and kindness.")
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=sorted({t for _, t in HEROES}))
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=sorted({t for _, t in HELPERS}))
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--trait", choices=TRAITS)
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
    prize = args.prize or rng.choice(list(PRIZES))
    need = args.need or rng.choice(list(NEEDS))
    hero_name, hero_type = (args.hero, args.hero_type) if args.hero and args.hero_type else rng.choice(HEROES)
    helper_name, helper_type = (args.helper, args.helper_type) if args.helper and args.helper_type else rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    if not select_help(PRIZES[prize], NEEDS[need]):
        raise StoryError("That prize and need do not make a believable intermission twist.")
    return StoryParams(hero=hero_name, hero_type=hero_type, helper=helper_name, helper_type=helper_type, prize=prize, need=need, trait=trait)


def _do_intermission(world: World, hero: Entity, prize: Entity) -> None:
    world.intermission = True
    hero.memes["anticipation"] = hero.memes.get("anticipation", 0.0) + 1.0
    world.say(f"At intermission, the little forest stage went still, and {hero.id} held {hero.pronoun('possessive')} {prize.label} close.")


def _twist(world: World, hero: Entity, helper: Entity, need: HelpNeed) -> None:
    world.twist = True
    hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1.0
    world.say(f"Then came the twist: {need.request}, and {helper.id} looked to {hero.id} for help.")


def _kindness(world: World, hero: Entity, helper: Entity, need: HelpNeed, prize: Entity) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1.0
    helper.memes["relief"] = helper.memes.get("relief", 0.0) + 1.0
    world.helped = True
    prize.meters["lost"] = prize.meters.get("lost", 0.0) + 1.0
    world.say(f"{hero.id} chose kindness and helped {helper.id} {need.fix}.")
    world.say(f"But while {hero.id} was helping, the {prize.label} was left behind.")


def _bad_ending(world: World, hero: Entity, prize: Entity, helper: Entity) -> None:
    hero.memes["sadness"] = hero.memes.get("sadness", 0.0) + 1.0
    world.say(f"When the show began again, the {prize.label} was gone, and {hero.id} did not win it.")
    world.say(f"Still, {helper.id} gave {hero.id} a small nod, and the night ended with a quiet lesson.")


def tell(params: StoryParams) -> World:
    world = World(Setting())
    hero = world.add(Entity(id=params.hero, type=params.hero_type, traits=[params.trait]))
    helper = world.add(Entity(id=params.helper, type=params.helper_type))
    prize = world.add(Entity(id="prize", type=PRIZES[params.prize].type, label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase, owner=hero.id))
    need = NEEDS[params.need]

    hero.memes["hope"] = 1.0
    prize.meters["held"] = 1.0

    world.say(f"{hero.id} was a {params.trait} little {hero.type} who loved the {prize.label}.")
    world.say(f"On the day of the show, {hero.id} sat near the stage and dreamed of keeping {prize.it()} forever.")
    world.para()
    _do_intermission(world, hero, prize)
    _twist(world, hero, helper, need)
    world.para()
    _kindness(world, hero, helper, need, prize)
    _bad_ending(world, hero, prize, helper)

    world.facts.update(hero=hero, helper=helper, prize=prize, need=need, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short fable for a young child about an intermission, a twist, and kindness.',
        f"Tell a story about {f['hero'].id}, a {f['hero'].type}, who wants to keep {f['prize'].label} safe but helps {f['helper'].id} during intermission.",
        f"Write a gentle bad-ending fable where {f['hero'].id} chooses kindness at the little forest stage.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, need = f["hero"], f["helper"], f["prize"], f["need"]
    return [
        QAItem(
            question=f"What happened at intermission in the story?",
            answer=f"The show paused at intermission, and {hero.id} was holding {hero.pronoun('possessive')} {prize.label} when a problem appeared.",
        ),
        QAItem(
            question=f"What was the twist in the story about {hero.id}?",
            answer=f"The twist was that {need.request}, so {helper.id} needed help right in the middle of the break.",
        ),
        QAItem(
            question=f"How did {hero.id} show kindness?",
            answer=f"{hero.id} stopped to help {helper.id} {need.fix}. That was kind, even though it cost {hero.id} the {prize.label}.",
        ),
        QAItem(
            question=f"Why is the ending a bad ending?",
            answer=f"It is a bad ending because the {prize.label} was lost and {hero.id} did not get the reward {hero.id} wanted, even after doing the right thing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an intermission?",
            answer="An intermission is a short pause in a play, show, or concert when everyone stops for a little while before it starts again.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means helping, sharing, or being gentle with someone else, even when it is not the easiest choice.",
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story, often with animals, that teaches a lesson at the end.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn in a story that changes what the characters thought would happen next.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    lines.append(f"intermission={world.intermission} twist={world.twist} helped={world.helped}")
    return "\n".join(lines)


CURATED = [
    StoryParams(hero="Milo", hero_type="mouse", helper="Otis", helper_type="owl", prize="seedcake", need="stuck_curtain", trait="gentle"),
    StoryParams(hero="Nina", hero_type="squirrel", helper="Mira", helper_type="mole", prize="bluebell", need="spilled_water", trait="curious"),
    StoryParams(hero="Pip", hero_type="rabbit", helper="Bram", helper_type="badger", prize="lantern", need="lost_child", trait="brave"),
]


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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
