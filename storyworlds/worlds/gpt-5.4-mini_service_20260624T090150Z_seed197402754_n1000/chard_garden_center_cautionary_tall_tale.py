#!/usr/bin/env python3
"""
chard_garden_center_cautionary_tall_tale.py
===========================================

A small storyworld about a garden center, a cautionary mistake, and a tall-tale
turn centered on chard.

The seed tale behind this world:
---
At a busy garden center, a child named Nora loved the rows of seedlings and the
wide greenhouse aisles. She found a chard plant with leaves as big as dinner
plates and thought it would be funny to hide behind it and race carts through
the herb benches.

Her grandpa warned her that the giant chard leaves were fragile and that the
carts would crush the roots if she went charging through the displays. Nora
laughed anyway, then knocked over a watering can and nearly toppled a whole
tray of young plants.

A clerk showed her how to lift the chard carefully and carry it to a safe pot.
Nora slowed down, apologized, and helped put everything right. By closing time,
the chard was still standing tall, and Nora remembered that even the tallest
leaves need gentle hands.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the garden center"
    affords: set[str] = field(default_factory=lambda: {"browse", "carry", "water"})


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    hazard: str
    damage: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    fragility: str
    region: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    action: str
    item: str
    name: str
    gender: str
    elder: str
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "garden_center": Setting(place="the garden center", affords={"browse", "carry", "water"}),
}

ACTIONS = {
    "dash": Action(
        id="dash",
        verb="dash down the aisles",
        gerund="dashing down the aisles",
        rush="race the carts between the benches",
        hazard="crushed roots",
        damage="knocked over trays and stomped roots",
        tags={"garden", "caution", "chard"},
    ),
    "hide": Action(
        id="hide",
        verb="hide behind the chard",
        gerund="hiding behind the chard",
        rush="duck behind the leaves",
        hazard="bent stems",
        damage="snapped leaves and bent stems",
        tags={"garden", "caution", "chard"},
    ),
    "lift": Action(
        id="lift",
        verb="lift the chard carefully",
        gerund="lifting the chard carefully",
        rush="hoist it without a plan",
        hazard="split roots",
        damage="split roots and torn pots",
        tags={"garden", "caution", "chard"},
    ),
}

ITEMS = {
    "chard": Item(
        id="chard",
        label="chard",
        phrase="a chard plant with leaves as wide as dinner plates",
        fragility="fragile",
        region="roots",
        tags={"chard", "garden", "green"},
    ),
    "seedlings": Item(
        id="seedlings",
        label="seedlings",
        phrase="a tray of young seedlings",
        fragility="fragile",
        region="trays",
        tags={"garden", "green"},
    ),
}

GIRL_NAMES = ["Nora", "Maya", "Lila", "Tess", "Ruby", "Zoe"]
BOY_NAMES = ["Eli", "Finn", "Theo", "Jack", "Noah", "Ben"]
TRAITS = ["curious", "bold", "restless", "cheerful", "impulsive", "mischievous"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for action in ACTIONS:
            for item in ITEMS:
                if place == "garden_center" and item == "chard" and action in {"dash", "hide", "lift"}:
                    combos.append((place, action, item))
    return combos


def prize_at_risk(action: Action, item: Item) -> bool:
    return item.id == "chard" and action.id in {"dash", "hide", "lift"}


def select_fix(action: Action, item: Item) -> Optional[str]:
    if item.id == "chard" and action.id == "lift":
        return "a garden cart and two careful hands"
    return None


def asp_facts() -> str:
    import asp
    lines = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, act in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for t in sorted(act.tags):
            lines.append(asp.fact("tagged", aid, t))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_fragile", iid))
        lines.append(asp.fact("region", iid, item.region))
        for t in sorted(item.tags):
            lines.append(asp.fact("tagged", iid, t))
    return "\n".join(lines)


ASP_RULES = r"""
risk(A,I) :- action(A), item(I), tagged(A,garden), tagged(I,garden), item_fragile(I).
fix(A,I) :- risk(A,I), A = lift.
valid(P,A,I) :- setting(P), affords(P, browse), risk(A,I), fix(A,I).
#show valid/3.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Garden-center cautionary tall tale with chard.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=["grandpa", "grandma"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.action and args.item:
        act, item = ACTIONS[args.action], ITEMS[args.item]
        if not prize_at_risk(act, item):
            raise StoryError("No story: that action does not put chard at risk.")
        if select_fix(act, item) is None:
            raise StoryError("No story: there is no sensible fix for that action and item.")
    combos = [c for c in valid_combos()
              if args.place in (None, c[0])
              and args.action in (None, c[1])
              and args.item in (None, c[2])]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, item = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["grandpa", "grandma"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, action=action, item=item, name=name, gender=gender, elder=elder, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    elder = world.add(Entity(id="elder", kind="character", type=params.elder, label=f"the {params.elder}"))
    chard = world.add(Entity(id="chard", type="plant", label="chard", phrase=ITEMS["chard"].phrase, caretaker=elder.id))
    seedlings = world.add(Entity(id="seedlings", type="plant", label="seedlings", phrase=ITEMS["seedlings"].phrase, caretaker=elder.id))
    hero.memes["curiosity"] = 1
    hero.memes["impulse"] = 1

    act = ACTIONS[params.action]

    world.say(
        f"At {world.setting.place}, {params.name} was a {params.trait} little {params.gender} who loved every shiny row of pots and herbs."
    )
    world.say(
        f"{hero.pronoun().capitalize()} stopped short when {hero.pronoun('subject')} saw {chard.phrase}; the leaves looked as big as wagon wheels in a storybook wind."
    )
    world.para()
    world.say(
        f"{params.name} wanted to {act.verb}, but {elder.pronoun().capitalize()} held up a steady hand and warned, "
        f'"That old chard is as {ITEMS["chard"].fragility} as a soap bubble in a hailstorm."'
    )
    world.say(
        f'"If you {act.rush}, you could bring about {act.damage}, and the little seedlings would never forgive the dust."'
    )
    hero.memes["defiance"] = 1
    world.say(
        f"But {params.name} only laughed a tall-tale laugh and went to {act.rush}, thinking the whole garden center would cheer."
    )
    world.say(
        f"The cart clipped a watering can with a clang like a spoon in a tin drum, and {seedlings.label} tipped sideways."
    )
    world.para()
    if params.action == "lift":
        world.say(
            f"Then {elder.label} showed {params.name} how to cradle the chard on both sides and roll in {seedlings.label} with a cart."
        )
    else:
        world.say(
            f"At last {elder.label} marched over and said the truth plain: '{params.name}, a giant leaf is no umbrella for a wild heart.'"
        )
        world.say(
            f"{params.name} blushed, picked up the watering can, and helped straighten every tray before the clerk even had to ask."
        )
        hero.memes["shame"] = 1
    hero.memes["regret"] = 1
    world.say(
        f"By closing time, the chard still stood tall, the seedlings were lined up like little soldiers, and {params.name} had learned to move gentle in a place full of growing things."
    )
    world.facts = {
        "hero": hero,
        "elder": elder,
        "chard": chard,
        "seedlings": seedlings,
        "action": act,
        "resolved": True,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, elder, act = f["hero"], f["elder"], f["action"]
    return [
        'Write a short cautionary tall tale set in a garden center that includes the word "chard".',
        f"Tell a child-friendly story where {hero.id} wants to {act.verb} but {elder.label} warns that the chard is fragile.",
        f"Write a tall tale about {hero.id}, {act.gerund}, and a garden center lesson about gentle hands.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, chard, act = f["hero"], f["elder"], f["chard"], f["action"]
    return [
        QAItem(question=f"Who wanted to {act.verb} at the garden center?", answer=f"{hero.id} wanted to {act.verb}."),
        QAItem(question=f"What plant made the story turn into a cautionary warning?", answer=f"The chard made the warning feel important because it was fragile."),
        QAItem(question=f"Who gave the warning about the chard?", answer=f"{elder.label.capitalize()} gave the warning and reminded {hero.id} to be careful."),
        QAItem(question=f"What did {hero.id} learn by the end?", answer=f"{hero.id} learned to slow down, use gentle hands, and help put everything right."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is chard?",
            answer="Chard is a leafy vegetable with big green leaves and sturdy stems, often grown in gardens and sold in garden centers.",
        ),
        QAItem(
            question="What is a garden center?",
            answer="A garden center is a store where people buy plants, seeds, soil, pots, and tools for growing things.",
        ),
        QAItem(
            question="Why should people handle fragile plants carefully?",
            answer="Fragile plants can bend, break, or lose roots if they are rushed or knocked around, so gentle hands keep them healthy.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden_center", action="dash", item="chard", name="Nora", gender="girl", elder="grandpa", trait="curious"),
    StoryParams(place="garden_center", action="hide", item="chard", name="Milo", gender="boy", elder="grandma", trait="impulsive"),
    StoryParams(place="garden_center", action="lift", item="chard", name="Tess", gender="girl", elder="grandpa", trait="bold"),
]


def explain_rejection(action: Action, item: Item) -> str:
    return f"(No story: {action.gerund} does not fit the cautionary chard setup.)"


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


def asp_verify_run() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify_run())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(f"{len(set(asp.atoms(model, 'valid')))} compatible combos:")
        for combo in sorted(set(asp.atoms(model, "valid"))):
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.name}: {p.action} at {p.place} (item: {p.item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
