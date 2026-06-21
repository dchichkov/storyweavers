#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/lament_expensive_intercept_sharing_moral_value_slice.py
========================================================================================

A small slice-of-life storyworld about sharing something expensive, a little
lament, and a timely intercept that turns a selfish moment into a kind one.

Seed words:
- lament
- expensive
- intercept

Features:
- Sharing
- Moral Value

Style:
- Slice of Life
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
VALUE_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class ShopItem:
    id: str
    label: str
    phrase: str
    price: int
    shareable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    shop_item: str
    sharer_name: str
    sharer_type: str
    companion_name: str
    companion_type: str
    parent_type: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_lament(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.memes["lament"] >= THRESHOLD:
            sig = ("lament", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["softness"] += 1
            out.append("__lament__")
    return out


def _r_share(world: World) -> list[str]:
    out = []
    owner = world.get("sharer")
    item = world.get("item")
    companion = world.get("companion")
    if owner.memes["sharing"] >= THRESHOLD and item.meters["pieces"] >= 2:
        sig = ("share",)
        if sig not in world.fired:
            world.fired.add(sig)
            companion.memes["care"] += 1
            owner.memes["joy"] += 1
            out.append("__share__")
    return out


def _r_value(world: World) -> list[str]:
    out = []
    family = world.get("parent")
    if family.memes["moral_value"] >= THRESHOLD:
        sig = ("value",)
        if sig not in world.fired:
            world.fired.add(sig)
            family.meters["pride"] += 1
            out.append("__value__")
    return out


CAUSAL_RULES = [_r_lament, _r_share, _r_value]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SHOP = {
    "cake": ShopItem("cake", "strawberry cake", "a slice of strawberry cake", 8, True, {"sweet", "share"}),
    "pie": ShopItem("pie", "apple pie", "a warm apple pie slice", 7, True, {"sweet", "share"}),
    "bread": ShopItem("bread", "buttery bread", "a buttery bread roll", 5, True, {"share"}),
}

PLACES = {
    "bakery": "the corner bakery",
    "market": "the little market",
    "cafe": "the quiet cafe",
}

NAMES_GIRL = ["Mina", "Lena", "Maya", "Ivy", "Nora", "Ada"]
NAMES_BOY = ["Noah", "Eli", "Finn", "Theo", "Leo", "Jack"]


def valid_combos() -> list[tuple[str]]:
    return [(sid,) for sid in SHOP if SHOP[sid].shareable]


def setup_story(world: World, params: StoryParams) -> None:
    item = SHOP[params.shop_item]
    sharer = world.add(Entity(id="sharer", kind="character", type=params.sharer_type, role="sharer"))
    companion = world.add(Entity(id="companion", kind="character", type=params.companion_type, role="companion"))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_type, role="parent", label="the parent"))
    shared = world.add(Entity(id="item", kind="thing", type="food", label=item.label))
    shared.meters["pieces"] = 2

    world.facts.update(item=item, place=PLACES[params.shop_item if params.shop_item in PLACES else "bakery"])
    world.facts.update(sharer=sharer, companion=companion, parent=parent, shared=shared)


def tell(world: World, params: StoryParams) -> None:
    item = SHOP[params.shop_item]
    sharer = world.get("sharer")
    companion = world.get("companion")
    parent = world.get("parent")
    shared = world.get("item")

    sharer.id = params.sharer_name
    companion.id = params.companion_name

    sharer.memes["want"] += 1
    companion.memes["lament"] += 1
    parent.memes["moral_value"] += 1

    world.say(
        f"After school, {params.sharer_name} and {params.companion_name} walked to {PLACES['bakery']}."
    )
    world.say(
        f"In the window was {item.phrase}, and it looked expensive enough that {params.sharer_name} had only one to share."
    )
    world.say(
        f'{params.companion_name} gave a small lament. "I wish there were two," {companion.pronoun()} said.'
    )
    world.para()
    world.say(
        f'{params.sharer_name} looked at the box, then at {params.companion_name}, and decided to share anyway.'
    )
    sharer.memes["sharing"] += 1
    if item.id == "cake":
        world.say(
            f"They cut the cake into two neat pieces so each child could have a fair bite."
        )
    else:
        world.say(
            f"They split the food into two even portions and put one half on each napkin."
        )

    world.para()
    if item.id == "cake":
        companion.meters["hands"] += 1
    else:
        companion.meters["hands"] += 1

    # Intercept beat: something nearly spoiled the moment, but a child stops it in time.
    world.say(
        f"Just then, a strong breeze tried to tip the shared treat over the table edge."
    )
    companion.memes["alert"] += 1
    world.say(
        f"{params.companion_name} reached out and intercepted it before it fell."
    )
    world.say(
        f'The parent smiled. "That was a kind thing to do," {parent.pronoun()} said. "Sharing and helping each other matters."'
    )

    world.para()
    propagate(world, narrate=False)
    world.say(
        f"By the time they sat down, both children had a piece, the box was lighter, and the afternoon felt warm and easy."
    )
    world.say(
        f"{params.sharer_name} was glad they had shared, and {params.companion_name} was glad the treat had been saved."
    )


def generate(params: StoryParams) -> StorySample:
    if params.shop_item not in SHOP:
        raise StoryError("Unknown shop item.")
    world = World()
    setup_story(world, params)
    tell(world, params)
    story = world.render()
    prompts = [
        f"Write a slice-of-life story about sharing {SHOP[params.shop_item].phrase} at a small shop.",
        f"Tell a gentle story where {params.sharer_name} shares something expensive and a child intercepts a mishap.",
        f"Write a story that includes the words lament, expensive, and intercept, and ends with a moral lesson about sharing.",
    ]
    story_qa = [
        QAItem(
            question="Why did the second child give a lament?",
            answer="The second child wanted more than one piece, but there was only one expensive treat to share. The story turns that wanting into kindness when the first child chooses to split it evenly."
        ),
        QAItem(
            question="What did the children do when the treat was in danger?",
            answer="They intercepted it before it fell off the edge of the table. That quick help saved the shared food and showed that they were looking out for each other."
        ),
        QAItem(
            question="What moral value does the story show?",
            answer="It shows that sharing matters, especially when something is expensive or hard to get. The ending makes that value visible because both children get to enjoy it together."
        ),
    ]
    world_qa = [
        QAItem(
            question="What does expensive mean?",
            answer="Expensive means it costs a lot of money. People often share expensive things carefully because they are special and not easy to replace."
        ),
        QAItem(
            question="What does intercept mean?",
            answer="Intercept means to stop something by catching it before it reaches where it was going. A child might intercept a falling cup or a rolling snack to keep it safe."
        ),
        QAItem(
            question="Why is sharing a good thing?",
            answer="Sharing is a good thing because it helps everyone feel included. It can also make a small treat feel happier, because more than one person gets to enjoy it."
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={dict(meters)}")
            if memes:
                bits.append(f"memes={dict(memes)}")
            if e.role:
                bits.append(f"role={e.role}")
            print(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print()
        print("== story qa ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}\nA: {q.answer}")
        print()
        print("== world qa ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}\nA: {q.answer}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about sharing and moral value.")
    ap.add_argument("--shop-item", choices=SHOP)
    ap.add_argument("--name")
    ap.add_argument("--companion-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    shop_item = args.shop_item or rng.choice(sorted(SHOP))
    sharer_type = args.gender or rng.choice(["girl", "boy"])
    sharer_name = args.name or rng.choice(NAMES_GIRL if sharer_type == "girl" else NAMES_BOY)
    companion_type = "boy" if sharer_type == "girl" else "girl"
    companion_name = args.companion_name or rng.choice(NAMES_BOY if companion_type == "boy" else NAMES_GIRL)
    parent_type = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        shop_item=shop_item,
        sharer_name=sharer_name,
        sharer_type=sharer_type,
        companion_name=companion_name,
        companion_type=companion_type,
        parent_type=parent_type,
    )


ASP_RULES = r"""
shareable(Item) :- item(Item), can_share(Item).
good_story(Item) :- shareable(Item).
moral_value :- shared(Item), help(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, item in SHOP.items():
        lines.append(asp.fact("item", sid))
        if item.shareable:
            lines.append(asp.fact("can_share", sid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show good_story/1."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    rc = 0
    try:
        import asp
        if set(asp_valid_combos()) == set(valid_combos()):
            print("OK: ASP and Python valid_combos() match.")
        else:
            rc = 1
            print("MISMATCH: ASP and Python valid_combos() differ.")
        sample = generate(
            StoryParams(
                shop_item=sorted(SHOP)[0],
                sharer_name="Mina",
                sharer_type="girl",
                companion_name="Noah",
                companion_type="boy",
                parent_type="mother",
            )
        )
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"VERIFY FAILED: {e}")
        return 1 if rc == 0 else rc
    return rc


CURATED = [
    StoryParams(shop_item="cake", sharer_name="Mina", sharer_type="girl", companion_name="Noah", companion_type="boy", parent_type="mother"),
    StoryParams(shop_item="pie", sharer_name="Eli", sharer_type="boy", companion_name="Maya", companion_type="girl", parent_type="father"),
    StoryParams(shop_item="bread", sharer_name="Nora", sharer_type="girl", companion_name="Leo", companion_type="boy", parent_type="mother"),
]


def valid_story(params: StoryParams) -> bool:
    return params.shop_item in SHOP and SHOP[params.shop_item].shareable


def generate_from_params(params: StoryParams) -> StorySample:
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show good_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible items:", ", ".join(x[0] for x in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
