#!/usr/bin/env python3
"""
storyworlds/worlds/merchant_playground_foreshadowing_surprise_humor_comedy.py
=============================================================================

A small playground comedy storyworld about a merchant, a curious child, and a
surprise that was foreshadowed all along.

The world model tracks:
- physical meters: carrying, tired, dusty, shiny, sticky, dropped
- emotional memes: eagerness, suspicion, delight, embarrassment, relief

Premise:
A merchant sets up a tiny stand at the playground and tries to sell playful
trinkets.

Tension:
A child wants something fun, but the merchant keeps hinting that the "special
surprise" is not what it seems.

Turn:
The hinted surprise arrives in a silly way that changes who wants what.

Resolution:
The merchant and child laugh together, and the playground ends brighter than it
started.
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the playground"
    affords: set[str] = field(default_factory=set)


@dataclass
class Goods:
    id: str
    label: str
    phrase: str
    price: str
    surprise: str
    foreshadow: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


@dataclass
class StoryParams:
    merchant_name: str
    child_name: str
    child_gender: str
    item: str
    seed: Optional[int] = None


SETTINGS = {
    "playground": Setting(place="the playground", affords={"sell", "bargain", "pretend"}),
}

ITEMS = {
    "balloon": Goods(
        id="balloon",
        label="balloon",
        phrase="a bright balloon shaped like a fish",
        price="one shiny coin",
        surprise="the balloon squeaks like a duck when squeezed",
        foreshadow="it kept making tiny squeaky breaths in the merchant's bag",
        tags={"balloon", "squeak", "surprise"},
    ),
    "spoon": Goods(
        id="spoon",
        label="spoon",
        phrase="a silver spoon with a ribbon tied on it",
        price="two small coins",
        surprise="the spoon turns out to be a wind-up spoon that tap-dances",
        foreshadow="it had little dancing feet drawn on the wrapper",
        tags={"spoon", "dance", "surprise"},
    ),
    "kite": Goods(
        id="kite",
        label="kite",
        phrase="a paper kite with a smiling face",
        price="three little coins",
        surprise="the kite is actually a tiny map of the playground",
        foreshadow="its string kept pointing toward the slide on purpose",
        tags={"kite", "map", "surprise"},
    ),
    "cookie": Goods(
        id="cookie",
        label="cookie",
        phrase="a huge cookie in a paper bag",
        price="one coin and a laugh",
        surprise="the cookie is shaped like a mitten and keeps crumbling into jokes",
        foreshadow="crumbs kept spelling out silly shapes inside the bag",
        tags={"cookie", "crumb", "surprise"},
    ),
}

NAMES = {
    "girl": ["Mia", "Nora", "Lily", "Ava", "Zoe"],
    "boy": ["Ben", "Leo", "Finn", "Max", "Theo"],
}
MERCHANT_NAMES = ["Milo", "Rina", "Jun", "Penny", "Arlo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A playground comedy about a merchant and a surprise.")
    ap.add_argument("--merchant-name", choices=MERCHANT_NAMES)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--item", choices=ITEMS)
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


def valid_combos() -> list[tuple[str, str]]:
    return [("playground", item_id) for item_id in ITEMS]


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "playground"), asp.fact("affords", "playground", "sell")]
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("surprise", item_id))
        for tag in sorted(item.tags):
            lines.append(asp.fact("tag", item_id, tag))
    return "\n".join(lines)


ASP_RULES = r"""
valid(playground, I) :- setting(playground), item(I), surprise(I).
#show valid/2.
"""


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
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    item = args.item or rng.choice(sorted(ITEMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(NAMES[gender])
    merchant_name = args.merchant_name or rng.choice(MERCHANT_NAMES)
    return StoryParams(
        merchant_name=merchant_name,
        child_name=child_name,
        child_gender=gender,
        item=item,
    )


def _do_story(world: World, params: StoryParams) -> None:
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name))
    merchant = world.add(Entity(id="merchant", kind="character", type="merchant", label=params.merchant_name))
    goods = world.add(Entity(
        id="goods",
        kind="thing",
        type=params.item,
        label=ITEMS[params.item].label,
        phrase=ITEMS[params.item].phrase,
        owner=merchant.id,
    ))

    child.memes["curiosity"] = 1
    merchant.memes["cheer"] = 1

    world.say(f"{child.label} went to the playground and found {merchant.label}, a merchant with a tiny stand.")
    world.say(f"{merchant.label} smiled and held up {goods.phrase}. \"Step right up,\" {merchant.pronoun()} said, \"for {goods.label} and a surprise.\"")
    world.say(f"{child.label} leaned closer. {ITEMS[params.item].foreshadow.capitalize()}")

    world.para()
    child.memes["desire"] = 1
    merchant.memes["mischief"] = 1
    world.say(f"{child.label} wanted the {goods.label} right away, because it looked fun and a little bit silly.")
    world.say(f"{merchant.label} tapped the bag and whispered, \"The surprise is real, and it is not what you think.\"")
    world.say(f"That made {child.label} suspicious, but also curious enough to stay.")

    world.para()
    child.meters["waiting"] = 1
    merchant.meters["carrying"] = 1
    world.say(f"At last, the bag tipped over. Out popped the surprise: {ITEMS[params.item].surprise}.")
    world.say(f"{child.label} stared for one tiny second, then burst out laughing.")
    world.say(f"{merchant.label} laughed too, because the serious-looking sale had turned into the silliest thing at the playground.")

    world.para()
    child.memes["delight"] = 1
    child.memes["suspicion"] = 0
    merchant.memes["relief"] = 1
    world.say(f"{child.label} paid with a grin, and {merchant.label} gave {child.label} the {goods.label} with a bow.")
    world.say(f"By the end, the playground was full of giggles, and the surprise had become the best part of the day.")

    world.facts.update(
        child=child,
        merchant=merchant,
        goods=goods,
        item=ITEMS[params.item],
        setting=world.setting,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS["playground"])
    _do_story(world, params)
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
    child = f["child"]
    merchant = f["merchant"]
    goods = f["goods"]
    return [
        "Write a short comedy story for a young child set at a playground, about a merchant and a surprising item.",
        f"Tell a playful story where {child.label} meets {merchant.label} at the playground and buys {goods.phrase}.",
        f"Write a story with foreshadowing, surprise, and humor in which a merchant sells a {goods.label} at the playground.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    merchant = f["merchant"]
    goods = f["goods"]
    item = f["item"]
    return [
        QAItem(
            question=f"Who met {child.label} at the playground?",
            answer=f"{child.label} met {merchant.label}, a merchant with a tiny stand.",
        ),
        QAItem(
            question=f"What did {merchant.label} keep hinting about while showing the {goods.label}?",
            answer=f"{merchant.label} kept hinting that there was a surprise, and the item's foreshadowing made {child.label} curious.",
        ),
        QAItem(
            question=f"What was the surprise about the {goods.label}?",
            answer=f"The surprise was that {item.surprise}. That silly twist made the sale funny instead of serious.",
        ),
        QAItem(
            question=f"How did {child.label} feel at the end?",
            answer=f"{child.label} ended up laughing and delighted, because the surprise turned into a joke they could share with {merchant.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a merchant?",
            answer="A merchant is a person who sells things to other people.",
        ),
        QAItem(
            question="What is a playground?",
            answer="A playground is a place where children can play, climb, swing, and run around.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a clue that hints something important or surprising may happen later.",
        ),
        QAItem(
            question="Why can humor make a story fun to read?",
            answer="Humor makes a story fun because it gives readers something silly or unexpected to laugh about.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(merchant_name="Milo", child_name="Mia", child_gender="girl", item="balloon"),
    StoryParams(merchant_name="Rina", child_name="Leo", child_gender="boy", item="kite"),
    StoryParams(merchant_name="Jun", child_name="Nora", child_gender="girl", item="cookie"),
    StoryParams(merchant_name="Penny", child_name="Ben", child_gender="boy", item="spoon"),
]


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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, item) combos:\n")
        for setting, item in combos:
            print(f"  {setting:12} {item}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.merchant_name} and {p.child_name} with {p.item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
