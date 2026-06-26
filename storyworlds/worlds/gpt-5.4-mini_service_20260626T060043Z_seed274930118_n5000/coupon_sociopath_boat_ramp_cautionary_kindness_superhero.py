#!/usr/bin/env python3
"""
A standalone storyworld: a small superhero story at the boat ramp.

Premise:
- A young hero loves helping people launch boats at the boat ramp.
- A coupon can pay for a special needed item.
- A mean, selfish sociopath-like bully tries to take advantage of others.
- The hero uses cautionary thinking and kindness to solve the problem.

World logic:
- The boat ramp can get slippery.
- A coupon can be used to get a safety cone, rope, or snack bundle.
- If someone rushes near the edge without caution, they may slip or block the ramp.
- Kindness can calm the crowd and redirect the problem into help.

This file is self-contained and follows the storyworld contract.
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
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the boat ramp"
    afford: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    verb: str
    gerund: str
    hazard: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Aid:
    id: str
    label: str
    prep: str
    tail: str
    covers: set[str]
    guards: set[str]


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
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def _say_name(ent: Entity) -> str:
    return ent.label or ent.id


def predict_hazard(world: World, hero: Entity, goal: Goal, prize_id: str) -> dict:
    sim = world.copy()
    do_goal(sim, sim.get(hero.id), goal, narrate=False)
    prize = sim.get(prize_id)
    return {
        "soiled": bool(prize.meters.get("wet", 0.0) >= THRESHOLD or prize.meters.get("dirty", 0.0) >= THRESHOLD),
        "blocked": bool(sim.facts.get("blocked", False)),
    }


def do_goal(world: World, hero: Entity, goal: Goal, narrate: bool = True) -> None:
    hero.meters[goal.hazard] = hero.meters.get(goal.hazard, 0.0) + 1.0
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1.0
    if narrate:
        world.say(f"{_say_name(hero)} wanted to {goal.verb} at the boat ramp.")


def spread_slip(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters.get("slip", 0.0) < THRESHOLD:
            continue
        if ("slip", e.id) in world.fired:
            continue
        world.fired.add(("slip", e.id))
        e.memes["fear"] = e.memes.get("fear", 0.0) + 1.0
        out.append(f"The wet ramp looked tricky, and {_say_name(e)} had to slow down.")
    return out


def warn_and_block(world: World, hero: Entity, villain: Entity, goal: Goal, prize: Prize) -> None:
    hero.memes["caution"] = hero.memes.get("caution", 0.0) + 1.0
    world.facts["blocked"] = True
    world.say(
        f"{_say_name(hero)} noticed the danger first and held up a hand. "
        f'"Careful!" {hero.pronoun().capitalize()} said. "The ramp is slippery, and we do not want {prize.label} getting ruined."'
    )
    villain.memes["greed"] = villain.memes.get("greed", 0.0) + 1.0
    world.say(
        f"A selfish bully tried to push ahead and grab the best spot, acting like a real sociopath who did not care who got hurt."
    )


def kindness_turn(world: World, hero: Entity, villain: Entity) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1.0
    villain.memes["ashamed"] = villain.memes.get("ashamed", 0.0) + 1.0
    world.say(
        f"{_say_name(hero)} did not yell. Instead, {hero.pronoun()} offered a kind smile and pointed to a safer line."
    )
    world.say(
        f"That gentle choice made the bully pause, lower {villain.pronoun('possessive')} shoulders, and back up."
    )


def use_coupon(world: World, hero: Entity, prize: Prize, aid_def: Aid) -> None:
    aid = world.add(Entity(
        id=aid_def.id,
        type="thing",
        label=aid_def.label,
        owner=hero.id,
    ))
    aid.worn_by = hero.id
    world.say(
        f"{_say_name(hero)} pulled out a coupon and used it to get {aid_def.label}."
    )
    world.say(
        f"With that help, {hero.pronoun()} could keep {prize.label} safe while moving near the water."
    )


def resolve(world: World, hero: Entity, villain: Entity, goal: Goal, prize: Prize, aid_def: Aid) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    world.say(
        f"Together, they used the {aid_def.label}, and the ramp felt calmer at once."
    )
    world.say(
        f"In the end, {_say_name(hero)} finished {goal.gerund}, {prize.label} stayed clean, and even the bully had to wait patiently."
    )


SETTING = Setting(place="the boat ramp", afford={"launch", "walk", "help"})

GOALS = {
    "launch": Goal(
        id="launch",
        verb="help launch the boat",
        gerund="helping launch the boat",
        hazard="slip",
        risk="wet",
        keyword="boat",
        tags={"water", "ramp", "safety"},
    ),
    "walk": Goal(
        id="walk",
        verb="walk down by the dock",
        gerund="walking by the water",
        hazard="slip",
        risk="wet",
        keyword="ramp",
        tags={"water", "ramp", "safety"},
    ),
}

PRIZES = {
    "couponbook": Prize(
        id="couponbook",
        label="coupon book",
        phrase="a bright coupon book",
        region="torso",
    ),
    "snackbag": Prize(
        id="snackbag",
        label="snack bag",
        phrase="a little snack bag",
        region="hand",
    ),
    "safetyvest": Prize(
        id="safetyvest",
        label="safety vest",
        phrase="a neon safety vest",
        region="torso",
    ),
}

AIDS = {
    "cone": Aid(
        id="cone",
        label="a bright safety cone",
        prep="place the cone near the edge",
        tail="set the cone by the slippery spot",
        covers={"path"},
        guards={"slip"},
    ),
    "vest": Aid(
        id="vest",
        label="a safety vest",
        prep="wear the vest before walking closer",
        tail="put on the vest and stepped more carefully",
        covers={"torso"},
        guards={"slip"},
    ),
    "rope": Aid(
        id="rope",
        label="a red rope line",
        prep="tie the rope across the risky edge",
        tail="tied the rope where people could see it",
        covers={"path"},
        guards={"slip"},
    ),
}

HERO_NAMES = ["Milo", "Tessa", "Ruby", "Nina", "Jasper", "Ivy"]
VILLAIN_NAMES = ["Vince", "Brute", "Rick", "Dale"]
TRAITS = ["brave", "caring", "steady", "quick-thinking"]


@dataclass
class StoryParams:
    place: str
    goal: str
    prize: str
    hero: str
    villain: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in {"boat_ramp": SETTING}.items():
        for g in GOALS:
            for p in PRIZES:
                combos.append((place, g, p))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero cautionary kindness story at the boat ramp.")
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--villain")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    goal = args.goal or rng.choice(list(GOALS))
    prize = args.prize or rng.choice(list(PRIZES))
    hero = args.name or rng.choice(HERO_NAMES)
    villain = args.villain or rng.choice(VILLAIN_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place="boat ramp", goal=goal, prize=prize, hero=hero, villain=villain, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTING)
    hero = world.add(Entity(id=params.hero, kind="character", type="boy", label=params.hero))
    villain = world.add(Entity(id=params.villain, kind="character", type="man", label=params.villain))
    prize = world.add(Entity(id="prize", type="thing", label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase, owner=hero.id))
    goal = GOALS[params.goal]

    world.say(f"{hero.id} was a small superhero with a {params.trait} heart.")
    world.say(f"{hero.id} loved the boat ramp because there were always people who needed help.")
    world.para()
    world.say(f"One day, {hero.id} came to {SETTING.place} with {prize.label} in hand.")
    world.say(f"{hero.id} wanted to {goal.verb}, but the ramp was wet and shiny.")
    warn_and_block(world, hero, villain, goal, prize)
    use_coupon(world, hero, prize, AIDS["cone"])
    kindness_turn(world, hero, villain)
    resolve(world, hero, villain, goal, prize, AIDS["cone"])

    world.facts.update(hero=hero, villain=villain, prize=prize, goal=goal)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a short superhero story set at the boat ramp about {hero.id}, caution, and kindness.",
        f"Tell a child-friendly story where a coupon helps a hero solve a slippery problem at the boat ramp.",
        f"Write a gentle superhero tale in which a brave helper stops a selfish bully and keeps everyone safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    villain = f["villain"]
    prize = f["prize"]
    goal = f["goal"]
    return [
        QAItem(
            question=f"Where did {hero.id}'s superhero story take place?",
            answer=f"It took place at the boat ramp, where the water made the ground look slippery.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at the boat ramp?",
            answer=f"{hero.id} wanted to {goal.verb}, but {hero.id} needed to be careful because the ramp was wet.",
        ),
        QAItem(
            question=f"Why did the hero use the coupon?",
            answer=f"{hero.id} used the coupon to get a safety cone, which helped everyone notice the slippery spot and keep {prize.label} safe.",
        ),
        QAItem(
            question=f"How did the hero treat the selfish bully?",
            answer=f"Instead of being mean back, {hero.id} stayed kind, which helped the bully calm down and wait his turn.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the ramp was safer, {hero.id} finished helping, and {prize.label} stayed clean.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a coupon?",
            answer="A coupon is a paper or code that lets you get something for less money or for free.",
        ),
        QAItem(
            question="Why should people be careful at a boat ramp?",
            answer="People should be careful at a boat ramp because wet surfaces can be slippery near the water.",
        ),
        QAItem(
            question="What does kindness do in a hard moment?",
            answer="Kindness can help people calm down, listen better, and choose safer actions.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== (1) Generation prompts ==")
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="boat ramp", goal="launch", prize="safetyvest", hero="Milo", villain="Vince", trait="brave"),
    StoryParams(place="boat ramp", goal="walk", prize="couponbook", hero="Tessa", villain="Brute", trait="caring"),
    StoryParams(place="boat ramp", goal="launch", prize="snackbag", hero="Ruby", villain="Rick", trait="steady"),
]


ASP_RULES = r"""
place(boat_ramp).
goal(launch).
goal(walk).
prize(couponbook).
prize(snackbag).
prize(safetyvest).
hero(milo).
hero(tessa).
hero(ruby).
villain(vince).
villain(brute).
villain(rick).
trait(brave).
trait(caring).
trait(steady).
trait(quick_thinking).

compatible(boat_ramp, G, P) :- goal(G), prize(P).
#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "boat_ramp")]
    for g in GOALS:
        lines.append(asp.fact("goal", g))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


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
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
