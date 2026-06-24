#!/usr/bin/env python3
"""
storyworlds/worlds/reindeer_delicious_minimize_twist_cautionary_folk_tale.py
============================================================================

A small folk-tale storyworld about a child, a reindeer, a delicious treat, and
a cautious twist that helps everyone minimize waste.

Seed image:
---
A child in a snowy village wants to offer a delicious berry cake to a reindeer.
The child is told to be careful because the cake is meant for the winter feast,
not for the noisy sled path. The child tries to feed the reindeer anyway, but
the reindeer startles at the crowd and nearly spills the cake. A wiser helper
suggests a twist: place the cake on a flat tray, share only a small piece, and
save the rest for the feast. The child listens, the reindeer calms down, and
the ending shows the cake still delicious and the mess minimized.

World logic:
- delicious food has a physical meter: crumbs/spilled/smushed
- caution can reduce waste by choosing a smaller, steadier serving
- a "twist" is a small change in method that turns a risky offering into a safe one
- emotional memes track hope, caution, worry, delight, relief
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    season: str
    folk_touch: str


@dataclass
class Food:
    id: str
    label: str
    phrase: str
    mess_kind: str
    fragile: bool = True


@dataclass
class TwistPlan:
    id: str
    label: str
    method: str
    reason: str
    saves: str
    reduces: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "village"),
        asp.fact("setting", "forest"),
        asp.fact("setting", "barn"),
        asp.fact("food", "berry_cake"),
        asp.fact("food", "honey_bread"),
        asp.fact("food", "spiced_turnip"),
        asp.fact("twist", "tray"),
        asp.fact("twist", "small_piece"),
        asp.fact("twist", "slow_steps"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
safe_offer(F, T) :- food(F), twist(T).
minimize_loss(T) :- twist(T).
"""

SETTINGS = {
    "village": Setting(place="the snowy village", season="winter", folk_touch="hushed chimneys"),
    "forest": Setting(place="the pine forest", season="winter", folk_touch="dark firs"),
    "barn": Setting(place="the red barn", season="snowy dusk", folk_touch="warm straw"),
}

FOODS = {
    "berry_cake": Food("berry_cake", "berry cake", "a delicious berry cake", "crumbs"),
    "honey_bread": Food("honey_bread", "honey bread", "a delicious honey bread loaf", "crumbs"),
    "spiced_turnip": Food("spiced_turnip", "spiced turnip tart", "a delicious spiced turnip tart", "smears"),
}

TWISTS = {
    "tray": TwistPlan("tray", "a flat tray", "place the food on a flat tray", "keeps it steady", "cake", "spills"),
    "small_piece": TwistPlan("small_piece", "a small piece", "share only a small piece", "keeps the rest for the feast", "rest", "waste"),
    "slow_steps": TwistPlan("slow_steps", "slow steps", "walk slowly and lower the plate", "keeps the reindeer calm", "food", "jostling"),
}

NAMES = ["Mira", "Anya", "Soren", "Pavel", "Elsa", "Niko", "Ivy", "Hanna"]
REINDEER_NAMES = ["Snowhorn", "Mistle", "Bracken", "Birch"]
HELPERS = ["grandmother", "old herder", "market aunt", "kind uncle"]
TRAITS = ["careful", "curious", "stubborn", "gentle", "lively"]


@dataclass
class StoryParams:
    setting: str
    food: str
    twist: str
    child: str
    child_type: str
    reindeer: str
    helper: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for f in FOODS:
            for t in TWISTS:
                combos.append((s, f, t))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale storyworld about reindeer, delicious food, and a cautious twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--reindeer-name", choices=REINDEER_NAMES)
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.food is None or c[1] == args.food)
              and (args.twist is None or c[2] == args.twist)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, food, twist = rng.choice(sorted(combos))
    child = args.name or rng.choice(NAMES)
    reindeer = args.reindeer_name or rng.choice(REINDEER_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    child_type = rng.choice(["girl", "boy"])
    return StoryParams(setting, food, twist, child, child_type, reindeer, helper, trait)


def _make_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(id=params.child, kind="character", type=params.child_type, label=params.child))
    rein = world.add(Entity(id=params.reindeer, kind="character", type="reindeer", label=params.reindeer))
    helper = world.add(Entity(id="helper", kind="character", type="adult", label=params.helper))
    food = world.add(Entity(id="food", type="food", label=FOODS[params.food].label, phrase=FOODS[params.food].phrase, plural=False))
    tray = world.add(Entity(id="tray", type="thing", label="tray"))
    world.facts.update(child=child, reindeer=rein, helper=helper, food=food, tray=tray, params=params)
    return world


def _story_turn(world: World, params: StoryParams) -> None:
    child: Entity = world.facts["child"]
    rein: Entity = world.facts["reindeer"]
    helper: Entity = world.facts["helper"]
    food: Entity = world.facts["food"]
    twist = TWISTS[params.twist]

    child.memes["hope"] = 1
    child.memes["delight"] = 1
    rein.memes["interest"] = 1

    world.say(f"In {world.setting.place}, beneath {world.setting.folk_touch}, {child.id} found {food.phrase}.")
    world.say(f"{child.id} wanted to give it to {rein.id}, because everyone said it was delicious.")
    world.para()

    child.memes["worry"] = 1
    rein.memes["worry"] = 1
    world.say(f"But {helper.label} frowned and said the feast food should be handled with care.")
    world.say(f'"Let us {twist.method}," {helper.label} said, "so we can {twist.reason}."')

    # physical consequence: direct offering causes spills; twist reduces it
    direct_spill = 1.0
    minimized = 0.0
    if params.twist == "tray":
        minimized = 0.2
    elif params.twist == "small_piece":
        minimized = 0.1
    elif params.twist == "slow_steps":
        minimized = 0.15

    child.meters["spilled"] = minimized
    food.meters["crumbs"] = minimized
    child.memes["relief"] = 1
    rein.memes["calm"] = 1
    world.para()

    world.say(f"{child.id} listened, set the {food.label} on the tray, and gave {rein.id} only a little piece.")
    world.say(f"The reindeer took it gently, and the rest stayed neat for the winter feast.")
    if minimized < direct_spill:
        world.say(f"The mess was minimized, and the cake still looked delicious.")
    else:
        world.say(f"Even so, the sharing stayed tidy and kind.")

    world.facts["twist_plan"] = twist
    world.facts["minimized"] = minimized


def tell(params: StoryParams) -> World:
    world = _make_world(params)
    _story_turn(world, params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short folk tale for a child named {p.child} about a delicious treat for a reindeer, with a cautious twist that minimizes waste.',
        f"Tell a gentle winter story where {p.child} and a reindeer named {p.reindeer} handle {FOODS[p.food].label} carefully.",
        f'Write a story with a wise helper who suggests a twist so the delicious food stays neat and the mess is minimized.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    food = FOODS[p.food]
    twist = TWISTS[p.twist]
    return [
        QAItem(
            question=f"What did {p.child} want to share with {p.reindeer}?",
            answer=f"{p.child} wanted to share {food.phrase} with {p.reindeer}. It was described as delicious, so the child was eager to offer it.",
        ),
        QAItem(
            question=f"Who gave the cautious advice in the story?",
            answer=f"{p.helper} gave the cautious advice and suggested a twist: {twist.method}. That helped everyone handle the food more carefully.",
        ),
        QAItem(
            question=f"How did the twist help the feast food?",
            answer=f"It kept the {food.label} steadier and minimized waste, so the treat stayed neat enough for the winter feast.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a reindeer?", answer="A reindeer is a deer that lives in cold northern places. Reindeer can pull sleds and walk through snow."),
        QAItem(question="What does delicious mean?", answer="Delicious means something tastes very good and pleasant to eat."),
        QAItem(question="What does minimize mean?", answer="Minimize means to make something as small as possible, like reducing a mess or waste."),
        QAItem(question="What is a twist in a story?", answer="A twist is a small change that turns the situation in a new way."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("\n== story qa ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}\nA: {q.answer}")
    parts.append("\n== world qa ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}\nA: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(out)


CURATED = [
    StoryParams("village", "berry_cake", "tray", "Mira", "girl", "Snowhorn", "grandmother", "careful"),
    StoryParams("forest", "honey_bread", "small_piece", "Soren", "boy", "Mistle", "old herder", "gentle"),
    StoryParams("barn", "spiced_turnip", "slow_steps", "Ivy", "girl", "Bracken", "market aunt", "curious"),
]


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show safe_offer/2.\n#show minimize_loss/1."))
    return sorted(set(asp.atoms(model, "safe_offer")))


def asp_verify() -> int:
    if len(asp_valid_combos()) != len(valid_combos()):
        print("Mismatch between ASP and Python combo counts.")
        return 1
    print("OK: ASP and Python agree on the simple reasonableness gate.")
    return 0


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show safe_offer/2.\n#show minimize_loss/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} ASP-compatible combos.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
