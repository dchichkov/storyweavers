#!/usr/bin/env python3
"""
A small adventure story world about nutrition, conflict, and a brave choice.

Seed tale idea:
- A child/adventurer wants to keep going on a quest.
- A guide warns that skipping a proper meal will make the child weak.
- The child resists, then notices trouble on the trail.
- They take a nutritious snack or meal, recover, and continue the adventure.

The world is intentionally small and constraint-checked: we only generate
stories where the food actually helps with the at-risk problem.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
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
    place: str
    path: str
    affordance: str


@dataclass
class Problem:
    id: str
    verb: str
    rush: str
    consequence: str
    weakness: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Food:
    id: str
    label: str
    phrase: str
    benefit: str
    fixes: set[str]
    taste: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    problem: str
    food: str
    name: str
    gender: str
    guide: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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


THRESHOLD = 1.0


SETTINGS = {
    "trail": Setting(place="the mountain trail", path="trail", affordance="journey"),
    "ruins": Setting(place="the sunlit ruins", path="stone path", affordance="journey"),
    "forest": Setting(place="the pine forest", path="forest path", affordance="journey"),
    "cove": Setting(place="the windy cove", path="coastal path", affordance="journey"),
}

PROBLEMS = {
    "hunger": Problem(
        id="hunger",
        verb="keep hiking without stopping for food",
        rush="race ahead",
        consequence="got shaky and slow",
        weakness="hunger",
        tags={"nutrition", "food"},
    ),
    "dizzy": Problem(
        id="dizzy",
        verb="climb without eating anything",
        rush="push on up the stones",
        consequence="started to wobble",
        weakness="dizziness",
        tags={"nutrition", "energy"},
    ),
    "tired": Problem(
        id="tired",
        verb="keep exploring without a snack",
        rush="dash on",
        consequence="felt too tired to go far",
        weakness="fatigue",
        tags={"nutrition", "energy"},
    ),
}

FOODS = {
    "apple": Food(
        id="apple",
        label="apple slices",
        phrase="a little box of apple slices",
        benefit="gave quick energy",
        fixes={"hunger", "tired"},
        taste="sweet and crisp",
        tags={"nutrition", "fruit"},
    ),
    "soup": Food(
        id="soup",
        label="warm soup",
        phrase="a steaming cup of vegetable soup",
        benefit="helped them feel steady and strong",
        fixes={"hunger", "dizzy", "tired"},
        taste="warm and cozy",
        tags={"nutrition", "vegetable"},
    ),
    "bread": Food(
        id="bread",
        label="trail bread",
        phrase="a small loaf of trail bread",
        benefit="kept their energy from dropping",
        fixes={"hunger", "tired"},
        taste="soft and filling",
        tags={"nutrition", "grain"},
    ),
    "nuts": Food(
        id="nuts",
        label="nuts and seeds",
        phrase="a pouch of nuts and seeds",
        benefit="gave strong lasting energy",
        fixes={"hunger", "dizzy", "tired"},
        taste="crunchy and rich",
        tags={"nutrition", "protein"},
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Ava", "Lena", "Zoe", "Ivy", "Maya", "Lily"]
BOY_NAMES = ["Finn", "Leo", "Theo", "Eli", "Max", "Noah", "Ben", "Sam"]
TRAITS = ["brave", "curious", "restless", "hopeful", "cheerful", "stubborn"]
GUIDES = ["mother", "father", "older sister", "older brother", "grandparent"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for pid, problem in PROBLEMS.items():
        for fid, food in FOODS.items():
            if pid in food.fixes:
                out.append((pid, fid))
    return out


def world_at_risk(problem: Problem, food: Food) -> bool:
    return problem.id in food.fixes


def choose_food(problem: Problem) -> Optional[Food]:
    for food in FOODS.values():
        if world_at_risk(problem, food):
            return food
    return None


def explain_rejection(problem: Problem, food: Food) -> str:
    return (
        f"(No story: {food.label} does not actually help with {problem.weakness}. "
        f"The adventure needs a real nutritional fix, so this pairing is rejected.)"
    )


def build_world(setting: Setting, problem: Problem, food: Food, name: str, gender: str,
                guide: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={}))
    helper = world.add(Entity(id="Guide", kind="character", type=guide, label=f"the {guide}"))
    meal = world.add(Entity(
        id="food",
        type=food.id,
        label=food.label,
        phrase=food.phrase,
        caretaker=helper.id,
    ))
    world.facts.update(hero=hero, helper=helper, food=meal, problem=problem, food_cfg=food, trait=trait)
    return world


def tell(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    food: Entity = f["food"]
    problem: Problem = f["problem"]
    food_cfg: Food = f["food_cfg"]
    trait = f["trait"]

    world.say(
        f"{hero.id} was a {trait} young adventurer who loved the road and every new turn in it."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted to {problem.verb}, because the trail looked exciting and wide open."
    )
    world.say(
        f"But {helper.label} frowned and warned that if {hero.id} kept going, {hero.pronoun('subject')} would {problem.consequence}."
    )
    world.para()
    world.say(
        f"{hero.id} only shook {hero.pronoun('possessive')} head and tried to {problem.rush}."
    )
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1.0
    hero.meters[problem.id] = hero.meters.get(problem.id, 0.0) + 1.0
    if hero.meters[problem.id] >= THRESHOLD:
        world.say(
            f"After a while, {hero.id} really did feel {problem.consequence}, and the adventure lost its sparkle."
        )
    world.para()
    world.say(
        f"Then {helper.label} opened {hero.pronoun('possessive')} pack and held out {food.phrase}."
    )
    world.say(
        f'"Eat this," {helper.label} said. "It will {food_cfg.benefit}."'
    )
    hero.meters[problem.id] = 0.0
    hero.meters["energy"] = hero.meters.get("energy", 0.0) + 1.0
    hero.memes["conflict"] = 0.0
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1.0
    world.say(
        f"{hero.id} ate {food.label}, which tasted {food_cfg.taste}, and soon {hero.pronoun('subject')} felt steady again."
    )
    world.say(
        f"With a full stomach and a lighter heart, {hero.id} and {helper.label} continued along {world.setting.place}."
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    problem: Problem = f["problem"]
    food: Entity = f["food"]
    return [
        f'Write a short adventure story for a young child that includes "{food.label}" and the word "nutrition".',
        f"Tell a story where {hero.id} wants to {problem.verb} but {helper.label} worries about {hero.pronoun('possessive')} energy.",
        f"Write a gentle conflict-and-resolution tale about a trail, a hungry adventurer, and a helpful snack.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    problem: Problem = f["problem"]
    food_cfg: Food = f["food_cfg"]
    return [
        QAItem(
            question=f"Why did {helper.label} worry about the trail adventure?",
            answer=(
                f"{helper.label} worried because if {hero.id} kept going, {hero.pronoun('subject')} would {problem.consequence}. "
                f"The problem was about nutrition, so {hero.id} needed real food, not just brave footsteps."
            ),
        ),
        QAItem(
            question=f"What helped {hero.id} feel strong again?",
            answer=(
                f"{food_cfg.phrase} helped {hero.id} feel steady again. It {food_cfg.benefit}, "
                f"so the trip could continue safely."
            ),
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=(
                f"At first {hero.id} was in conflict and wanted to push ahead without stopping. "
                f"By the end, {hero.id} had eaten and felt better, and the journey continued with a calmer heart."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    food_cfg: Food = f["food_cfg"]
    problem: Problem = f["problem"]
    out = [
        QAItem(
            question="What does nutrition mean?",
            answer=(
                "Nutrition means the food and drink living things use to grow, move, and stay healthy."
            ),
        ),
        QAItem(
            question="Why do adventurers carry snacks?",
            answer=(
                "Adventurers carry snacks because a small meal can keep their energy up on a long trip."
            ),
        ),
    ]
    if "fruit" in food_cfg.tags:
        out.append(QAItem(
            question="Why are fruit snacks helpful on a journey?",
            answer="Fruit snacks can give quick energy and are easy to carry in a pack.",
        ))
    if "protein" in food_cfg.tags:
        out.append(QAItem(
            question="Why do seeds and nuts help travelers?",
            answer="Seeds and nuts can give lasting energy, which is useful when a trail is long.",
        ))
    if problem.id == "dizzy":
        out.append(QAItem(
            question="What can happen when someone skips food for too long?",
            answer="They may feel dizzy, weak, or tired because their body has run low on fuel.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
chosen_food(F) :- food(F), fixes(F, P), problem(P).
valid_pair(P, F) :- problem(P), food(F), fixes(F, P).
#show valid_pair/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("weakness", pid, p.weakness))
    for fid, f in FOODS.items():
        lines.append(asp.fact("food", fid))
        for p in sorted(f.fixes):
            lines.append(asp.fact("fixes", fid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_pair/2."))
    return sorted(set(asp.atoms(model, "valid_pair")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} pairs).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world about nutrition and conflict.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--name")
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
    if args.problem and args.food:
        if not world_at_risk(PROBLEMS[args.problem], FOODS[args.food]):
            raise StoryError(explain_rejection(PROBLEMS[args.problem], FOODS[args.food]))
    combos = [c for c in valid_combos()
              if (args.problem is None or c[0] == args.problem)
              and (args.food is None or c[1] == args.food)]
    if not combos:
        raise StoryError("(No valid nutrition-conflict story matches the given options.)")
    problem, food = rng.choice(sorted(combos))
    pr = PROBLEMS[problem]
    fd = FOODS[food]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide = args.guide or rng.choice(GUIDES)
    trait = args.trait or rng.choice(TRAITS)
    place = args.place or rng.choice(list(SETTINGS))
    return StoryParams(place=place, problem=problem, food=food, name=name, gender=gender, guide=guide, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(
        SETTINGS[params.place],
        PROBLEMS[params.problem],
        FOODS[params.food],
        params.name,
        params.gender,
        params.guide,
        params.trait,
    )
    tell(world)
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
    StoryParams(place="trail", problem="hunger", food="apple", name="Mia", gender="girl", guide="mother", trait="brave"),
    StoryParams(place="ruins", problem="dizzy", food="soup", name="Finn", gender="boy", guide="father", trait="curious"),
    StoryParams(place="forest", problem="tired", food="bread", name="Ava", gender="girl", guide="older sister", trait="restless"),
    StoryParams(place="cove", problem="hunger", food="nuts", name="Leo", gender="boy", guide="grandparent", trait="hopeful"),
]


def asp_valid_pairs_with_story() -> list[tuple]:
    return asp_valid_pairs()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_pair/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_pairs_with_story()
        print(f"{len(pairs)} valid nutrition pairs:\n")
        for p, f in pairs:
            print(f"  {p:7} {f}")
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
            header = f"### {p.name}: {p.problem} with {p.food} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
