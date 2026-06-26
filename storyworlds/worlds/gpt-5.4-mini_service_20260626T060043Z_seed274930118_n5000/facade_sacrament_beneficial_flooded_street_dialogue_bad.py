#!/usr/bin/env python3
"""
storyworlds/worlds/facade_sacrament_beneficial_flooded_street_dialogue_bad.py
=============================================================================

A small pirate-tale story world set on a flooded street.

Premise:
- A young pirate and a chapel keeper try to carry a sacrament through a flooded
  street past a broken facade.
- They believe the sacrament is beneficial for the sick neighbors.
- The flood rises, the plan fails, and the story ends badly.

This world intentionally features:
- Dialogue
- A bad ending
- A child-facing pirate tone
- The seed words: facade, sacrament, beneficial
- A flooded street setting

The world is modeled as a tiny simulation with physical meters and emotional
memes. The prose is generated from state changes, not from a frozen template.
"""

from __future__ import annotations

import argparse
import copy
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def emo(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the flooded street"
    facade: str = "the chapel facade"
    tide: str = "the floodwater"
    affords: set[str] = field(default_factory=lambda: {"carry_sacrament", "cross_street"})


@dataclass
class Goal:
    id: str
    verb: str
    gerund: str
    mess: str
    zone: set[str]
    risk_noun: str
    risky_word: str = "flooded"
    tags: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]


GOAL = Goal(
    id="sacrament",
    verb="carry the sacrament to the chapel",
    gerund="carrying the sacrament",
    mess="wet",
    zone={"feet", "legs", "torso"},
    risk_noun="relic",
    tags={"sacrament", "beneficial", "facade"},
)

RELIC = Relic(
    id="sacrament",
    label="sacrament",
    phrase="a small silver sacrament box",
    region="torso",
)

GEAR = [
    Gear(
        id="tarpaulin",
        label="a tarpaulin",
        covers={"torso", "legs"},
        guards={"wet"},
        prep="wrap the sacrament in a tarpaulin first",
        tail="had wrapped the relic well enough to keep most of the spray off",
    )
]

SETTINGS = {
    "flooded_street": Setting(),
}

NAMES = ["Mara", "Finn", "Pip", "Tess", "Jory", "Nell"]
PIRATE_TITLES = ["deckhand", "matey", "young pirate", "little corsair"]


@dataclass
class StoryParams:
    place: str
    hero: str
    title: str
    seed: Optional[int] = None


ASP_RULES = r"""
risk(sacrament) :- goal(sacrament), zone(sacrament, torso).
flooded(street).
bad_end :- risk(sacrament), flood(street), no_safe_plan.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("goal", GOAL.id), asp.fact("flood", "street"), asp.fact("no_safe_plan")]
    for z in sorted(GOAL.zone):
        lines.append(asp.fact("zone", GOAL.id, z))
    for k in sorted(GOAL.tags):
        lines.append(asp.fact("tag", GOAL.id, k))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _risk_relic(goal: Goal, relic: Relic) -> bool:
    return relic.region in goal.zone


def _select_gear(goal: Goal, relic: Relic) -> Optional[Gear]:
    for gear in GEAR:
        if relic.region in gear.covers and goal.mess in gear.guards:
            return gear
    return None


def _flood_rises(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("attempted") and not world.facts.get("saved"):
        if ("flood", "rise") in world.fired:
            return []
        world.fired.add(("flood", "rise"))
        hero = world.get("hero")
        relic = world.get("relic")
        hero.meters["wet"] = hero.meters.get("wet", 0.0) + 1
        relic.meters["wet"] = relic.meters.get("wet", 0.0) + 1
        hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
        out.append("The floodwater climbed higher and slapped at their knees.")
        out.append(f"The little box got wet, and {relic.label} turned slippery in {hero.pronoun('possessive')} hands.")
    return out


def _lose_relic(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    relic = world.get("relic")
    if hero.meters.get("wet", 0.0) < THRESHOLD:
        return out
    if relic.meters.get("wet", 0.0) < THRESHOLD:
        return out
    if ("lose", relic.id) in world.fired:
        return out
    world.fired.add(("lose", relic.id))
    relic.memes["lost"] = relic.memes.get("lost", 0.0) + 1
    hero.memes["grief"] = hero.memes.get("grief", 0.0) + 1
    out.append(f"A nasty wave tore {relic.it()} away, and it vanished under the gray water.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_flood_rises, _lose_relic):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(hero_name: str, title: str) -> World:
    world = World(SETTINGS["flooded_street"])
    hero = world.add(Entity(id="hero", kind="character", type="boy", label=hero_name))
    keeper = world.add(Entity(id="keeper", kind="character", type="priest", label="Father Oren"))
    relic = world.add(Entity(
        id="relic", type="thing", label="sacrament", phrase=RELIC.phrase, caretaker=keeper.id
    ))
    world.add(Entity(id="facade", type="thing", label="facade", phrase="the cracked chapel facade"))

    world.facts.update(hero=hero, keeper=keeper, relic=relic, setting=world.setting, goal=GOAL)

    hero.memes["curiosity"] = 1
    keeper.memes["duty"] = 1
    relic.memes["hope"] = 1

    world.say(
        f"In the flooded street by the chapel facade, {hero_name} was a little {title} who liked to listen for trouble."
    )
    world.say(
        f"Father Oren tapped the box and said, \"This sacrament is beneficial, matey; it may help the sick folk down the lane.\""
    )
    world.say(
        f"{hero_name} grinned. \"Then let me carry it, Father. I know the street better than a gull knows a dock,\" {hero_name} said."
    )

    world.para()
    world.say(
        f"They stepped past the facade and into the water, where broken bricks hid under the brown waves."
    )
    world.say(
        f"\"Keep your boots high,\" Father Oren warned. \"A flooded street is a sneaky beast.\""
    )
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    world.facts["attempted"] = True
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"\"I can do it,\" {hero_name} said, but the current nudged at {hero_name} like a rough-handed pirate."
    )
    world.say(
        f"\"Nay,\" Father Oren muttered, reaching out. \"The water has the upper hand.\""
    )
    hero.memes["defiance"] = hero.memes.get("defiance", 0.0) + 1
    hero.meters["wet"] = hero.meters.get("wet", 0.0) + 1
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{hero_name} tried to keep the sacrament above the splash, but the street rolled and rocked."
    )
    world.say(
        f"\"Hold fast!\" Father Oren cried, yet the tide answered with a slap and a roar."
    )
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"When the water settled, the silver box was gone, and the chapel facade looked lonelier than a ship without sails."
    )
    world.say(
        f"{hero_name} stared at the empty palms and whispered, \"I thought it would be beneficial.\""
    )
    world.say(
        f"Father Oren put a hand on {hero_name}'s shoulder and said, \"A good wish still needs dry ground, lad.\""
    )
    hero.memes["grief"] = hero.memes.get("grief", 0.0) + 1
    world.facts["saved"] = False
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        "Write a short pirate tale with dialogue about a flooded street, a facade, and a sacrament.",
        f"Tell a child-friendly story where {hero.label} tries to carry a beneficial sacrament through floodwater and it ends badly.",
        "Use the words facade, sacrament, and beneficial in a story with a bad ending and a pirate voice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    keeper = world.get("keeper")
    relic = world.get("relic")
    return [
        QAItem(
            question="What was the story about?",
            answer=(
                f"It was about {hero.label}, Father Oren, and a sacrament on a flooded street by the chapel facade."
            ),
        ),
        QAItem(
            question="Why did Father Oren call the sacrament beneficial?",
            answer=(
                "He believed it could help the sick folk down the lane, so he wanted to carry it safely through the flood."
            ),
        ),
        QAItem(
            question="What went wrong in the end?",
            answer=(
                f"The floodwater rose, the sacrament box slipped away, and {relic.label} was lost under the water."
            ),
        ),
        QAItem(
            question="How did the pirate voice show up in the dialogue?",
            answer=(
                f"Father Oren called {hero.label} matey, and the tale used words like lad, gull, and sea-sounding warnings."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a facade?",
            answer="A facade is the front face of a building, like the outer wall people see first.",
        ),
        QAItem(
            question="What is a sacrament?",
            answer="A sacrament is a holy act or holy object used in some religious traditions.",
        ),
        QAItem(
            question="What does beneficial mean?",
            answer="Beneficial means helpful or good for someone.",
        ),
        QAItem(
            question="Why is a flooded street dangerous?",
            answer="A flooded street can hide holes, carry people off balance, and sweep away small things in the water.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"{e.id}: {e.type} {e.label} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def asp_valid() -> bool:
    import asp
    model = asp.one_model(asp_program("#show risk/1."))
    return ("sacrament",) in set(asp.atoms(model, "risk"))


def asp_verify() -> int:
    python_ok = _risk_relic(GOAL, RELIC) and _select_gear(GOAL, RELIC) is not None
    clingo_ok = asp_valid()
    if python_ok == clingo_ok:
        print("OK: ASP and Python gate agree.")
        return 0
    print(f"MISMATCH: python={python_ok} clingo={clingo_ok}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld set in a flooded street.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name")
    ap.add_argument("--title", choices=PIRATE_TITLES)
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
    place = args.place or "flooded_street"
    if place != "flooded_street":
        raise StoryError("This storyworld only supports the flooded street.")
    hero = args.name or rng.choice(NAMES)
    title = args.title or rng.choice(PIRATE_TITLES)
    return StoryParams(place=place, hero=hero, title=title, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.hero, params.title)
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
        print(asp_program("#show risk/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story pattern: sacrament carried through flooded street, but it ends badly.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(place="flooded_street", hero="Mara", title="young pirate", seed=base_seed)
        samples.append(generate(params))
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
