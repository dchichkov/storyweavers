#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/improvise_financial_basket_twist_fairy_tale.py
==============================================================================================================

A small fairy-tale story world about improvising, a financial worry, a basket,
and a twist that turns a careful plan into a happy ending.

Seed tale used to build the world model:
---
In a little hill village, a young baker named Mina had a problem. She needed a
silver coin to buy flour before dawn, but her money pouch was empty. Her granny
said the market would not wait, and the bread oven would go cold.

Mina looked around the cottage and spotted an old basket, a spool of ribbon,
and a few shiny beans from the windowsill. She improvised a plan: she would
carry sweet buns in the basket, walk to the fair, and trade them for a coin.

At the fair, a twist came. The basket's lining hid a tiny nest of gold beads
that had fallen from Granny's sewing box. Mina returned the beads, and the
laughing seamstress rewarded her with enough coins for flour and a little extra.

Causal state updates:
---
    financial worry -> character.memes["worry"] += 1
    improvised basket plan -> character.memes["hope"] += 1 ; basket.meters["use"] += 1
    basket used for carrying goods -> goods stay safe if basket is sound
    discovered hidden treasure twist -> character.memes["surprise"] += 1 ; worry lowers
    honest return of treasure -> helper.memes["gratitude"] += 1 ; hero.memes["pride"] += 1
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
    worn_by: Optional[str] = None
    plural: bool = False
    sound: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "granny", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    plural: bool = False


@dataclass
class Twist:
    id: str
    reveal: str
    reward: str
    tags: set[str] = field(default_factory=set)


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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SETTING = Setting(place="the village market", indoor=False, affords={"market", "fair"})
ACTIVITIES = {
    "market": Activity(
        id="market",
        verb="go to the market",
        gerund="walking to the market",
        rush="hurry down the lane",
        keyword="financial",
        tags={"financial", "market"},
    ),
    "fair": Activity(
        id="fair",
        verb="sell treats at the fair",
        gerund="selling sweet treats",
        rush="rush to the fair stall",
        keyword="basket",
        tags={"basket", "fair"},
    ),
}

TWISTS = {
    "hidden_beads": Twist(
        id="hidden_beads",
        reveal="the basket lining hid Granny's sewing beads",
        reward="the seamstress paid for the returned beads",
        tags={"basket", "financial"},
    ),
    "lost_coin": Twist(
        id="lost_coin",
        reveal="the basket had caught a lost silver coin under the berries",
        reward="the miller thanked the child with flour and a coin",
        tags={"financial", "basket"},
    ),
}

PRIZES = {
    "basket": Prize(label="basket", phrase="an old woven basket", type="basket"),
    "coins": Prize(label="coins", phrase="a few bright coins", type="coins", plural=True),
}

GIRL_NAMES = ["Mina", "Lina", "Nora", "Elsa", "Tilda", "Pippa"]
BOY_NAMES = ["Toby", "Jasper", "Owen", "Bram", "Milo", "Robin"]
TRAITS = ["clever", "gentle", "brave", "cheerful", "thoughtful"]


ASP_RULES = r"""
% A story is valid when the place supports the activity and the chosen twist
% mentions the same world theme.
valid(Place, Activity, Twist) :- affords(Place, Activity), theme(Twist, Activity).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "village_market"))
    lines.append(asp.fact("affords", "village_market", "market"))
    lines.append(asp.fact("affords", "village_market", "fair"))
    for a in ACTIVITIES.values():
        lines.append(asp.fact("activity", a.id))
        for t in sorted(a.tags):
            lines.append(asp.fact("theme", a.id, t))
    for t in TWISTS.values():
        lines.append(asp.fact("twist", t.id))
        for tag in sorted(t.tags):
            lines.append(asp.fact("theme", t.id, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in ["village_market"]:
        for act in ACTIVITIES:
            for twist in TWISTS:
                if place == "village_market" and ACTIVITIES[act].tags & TWISTS[twist].tags:
                    out.append((place, act, twist))
    return out


def asp_verify() -> int:
    a = set(asp_valid())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    twist: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale world of improvising a financial basket twist.")
    ap.add_argument("--place", choices=["village_market"], default=None)
    ap.add_argument("--activity", choices=ACTIVITIES, default=None)
    ap.add_argument("--prize", choices=PRIZES, default=None)
    ap.add_argument("--twist", choices=TWISTS, default=None)
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--name", default=None)
    ap.add_argument("--helper", choices=["granny", "baker", "miller", "seamstress"], default=None)
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
    combos = valid_combos()
    combos = [c for c in combos
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.twist is None or c[2] == args.twist)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, twist = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["granny", "baker", "miller", "seamstress"])
    trait = rng.choice(TRAITS)
    prize = args.prize or "basket"
    return StoryParams(place=place, activity=activity, prize=prize, twist=twist,
                       name=name, gender=gender, helper=helper, trait=trait)


def _setup_world(params: StoryParams) -> World:
    w = World(SETTING)
    hero = w.add(Entity(id=params.name, kind="character", type=params.gender))
    helper_type = params.helper
    helper = w.add(Entity(id="Helper", kind="character", type=helper_type, label=f"the {helper_type}"))
    basket = w.add(Entity(id="basket", type="basket", label="basket", phrase="an old woven basket"))
    coins = w.add(Entity(id="coins", type="coins", label="coins", phrase="a few bright coins", plural=True))
    hero.memes.update({"worry": 0.0, "hope": 0.0, "surprise": 0.0, "pride": 0.0})
    basket.meters["use"] = 0.0
    w.facts.update(hero=hero, helper=helper, basket=basket, coins=coins, params=params)
    return w


def tell(params: StoryParams) -> World:
    w = _setup_world(params)
    p = params
    hero = w.facts["hero"]
    helper = w.facts["helper"]
    basket = w.facts["basket"]
    coins = w.facts["coins"]
    act = ACTIVITIES[p.activity]
    twist = TWISTS[p.twist]

    w.say(f"Once in {w.setting.place}, a little {p.trait} {p.gender} named {p.name} woke with a financial worry.")
    w.say(f"{p.name} needed flour, but {hero.pronoun('possessive')} money pouch was nearly empty.")
    w.say(f"{hero.pronoun().capitalize()} looked at an old basket and decided to improvise.")
    hero.memes["worry"] += 1
    hero.memes["hope"] += 1
    basket.meters["use"] += 1

    w.para()
    w.say(f"So {p.name} set off {act.gerund}, carrying the basket toward the market.")
    w.say(f"{hero.pronoun().capitalize()} planned to {act.verb} and earn enough coins for flour.")
    if p.helper == "granny":
        w.say("Granny blessed the plan with a wink, saying that kind hands often find kind luck.")
    else:
        w.say(f"The {p.helper} nodded and said the market liked brave little plans.")

    w.para()
    w.say(f"At the fair, a twist waited: {twist.reveal}.")
    hero.memes["surprise"] += 1
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1)
    w.say(f"{p.name} returned the treasure at once, because the basket had only borrowed it by accident.")
    hero.memes["pride"] += 1
    helper.memes["gratitude"] = helper.memes.get("gratitude", 0.0) + 1

    w.para()
    w.say(f"{twist.reward}.")
    w.say(f"In the end, {p.name} bought flour, the basket stayed useful, and the little lane smelled like fresh bread.")
    w.facts["resolved"] = True
    w.facts["twist"] = twist
    return w


def generation_prompts(w: World) -> list[str]:
    p: StoryParams = w.facts["params"]
    return [
        f'Write a short fairy tale about a child who must improvise a financial plan with a basket.',
        f"Tell a story where {p.name} worries about money, uses an old basket, and encounters a twist at the market.",
        f'Write a gentle fairy tale using the words "improvise", "financial", and "basket".',
    ]


def story_qa(w: World) -> list[QAItem]:
    p: StoryParams = w.facts["params"]
    hero = w.facts["hero"]
    helper = w.facts["helper"]
    twist = w.facts["twist"]
    return [
        QAItem(
            question=f"Why did {p.name} improvise with the basket?",
            answer=f"{p.name} improvised because there was a financial worry and the money pouch was nearly empty, so the basket became part of a clever plan to earn flour money.",
        ),
        QAItem(
            question=f"What twist happened at the fair?",
            answer=f"The twist was that {twist.reveal}. That changed the plan from selling treats to returning the treasure honestly.",
        ),
        QAItem(
            question=f"How did {p.name} feel at the end?",
            answer=f"{p.name} felt proud and happier because {twist.reward}, and the bread plan worked out in the end.",
        ),
        QAItem(
            question=f"Who helped {p.name} along the way?",
            answer=f"{helper.label} helped by encouraging the plan and by being part of the happy ending when the treasure was returned.",
        ),
        QAItem(
            question=f"What stayed useful in the story?",
            answer="The basket stayed useful, because it helped carry the plan to the market and was still a good basket afterward.",
        ),
    ]


KNOWLEDGE = {
    "financial": [(
        "What does financial mean?",
        "Financial means having to do with money, paying, saving, buying, or earning coins and bills."
    )],
    "basket": [(
        "What is a basket?",
        "A basket is a container, often woven from reeds or straw, that can carry bread, fruit, flowers, or little treasures."
    )],
    "improvise": [(
        "What does improvise mean?",
        "To improvise means to make a plan or use something in a new way without preparing everything in advance."
    )],
    "twist": [(
        "What is a twist in a story?",
        "A twist is a surprise change that makes the story go in a new direction."
    )],
}


def world_knowledge_qa(w: World) -> list[QAItem]:
    tags = {"financial", "basket", "improvise", "twist"}
    out: list[QAItem] = []
    for tag in ["improvise", "financial", "basket", "twist"]:
        for q, a in KNOWLEDGE[tag]:
            out.append(QAItem(question=q, answer=a))
    return out


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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid())} compatible (place, activity, twist) combos:")
        for t in asp_valid():
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        params_list = [
            StoryParams(place="village_market", activity="market", prize="basket", twist="hidden_beads",
                        name="Mina", gender="girl", helper="granny", trait="clever"),
            StoryParams(place="village_market", activity="fair", prize="basket", twist="lost_coin",
                        name="Toby", gender="boy", helper="seamstress", trait="brave"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            params.seed = seed
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
