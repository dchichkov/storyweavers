#!/usr/bin/env python3
"""
storyworlds/worlds/rebate_humor_folk_tale.py
===========================================

A small folk-tale storyworld about a humble shopper, a tricky rebate, and a
humorous turn of fortune.

Seed tale:
---
Once in a small village, a careful grandmother bought a sturdy kettle from the
market. The peddler promised a rebate if she mailed a postcard and a tiny form
back to the shop. The grandmother followed the instructions, but the goat at the
gate chewed the postcard and the cat sat on the form.

The grandmother laughed, asked the peddler for help, and the peddler gave her a
new form and a fresh stamp. In the end, she mailed the rebate papers, got her
money back, and told the whole village that sometimes a silly mix-up can still
end well.

Causal state updates:
---
    purchase -> shopper owns item, merchant expects payment
    rebate offer -> rebate promise recorded for a purchased item
    lost/damaged paperwork -> rebate pending, frustration rises
    helper intervention -> frustration falls, confidence rises
    successful submission -> rebate paid, joy rises, humor remembered
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother", "aunt"}
        male = {"boy", "man", "father", "grandfather", "uncle", "merchant", "peddler"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Shop:
    place: str = "the market"


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    price: int
    rebate_amount: int
    requires_mail: bool = True


@dataclass
class Paperwork:
    id: str
    label: str
    phrase: str
    kind: str  # postcard / form / receipt
    can_be_chewed: bool = True
    can_be_sat_on: bool = True


class World:
    def __init__(self, shop: Shop) -> None:
        self.shop = shop
        self.entities: dict[str, Entity] = {}
        self.paper: dict[str, bool] = {}
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
        import copy
        clone = World(self.shop)
        clone.entities = copy.deepcopy(self.entities)
        clone.paper = dict(self.paper)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_chew(world: World) -> list[str]:
    out: list[str] = []
    goat = world.entities.get("goat")
    postcard = world.entities.get("postcard")
    if not goat or not postcard:
        return out
    if world.paper.get("postcard_chewed"):
        return out
    if goat.memes.get("mischief", 0) >= THRESHOLD and postcard.meters.get("near_goat", 0) >= THRESHOLD:
        world.paper["postcard_chewed"] = True
        world.fired.add(("chew", "postcard"))
        out.append("The goat at the gate chewed the postcard right into confetti.")
    return out


def _r_sit(world: World) -> list[str]:
    out: list[str] = []
    cat = world.entities.get("cat")
    form = world.entities.get("form")
    if not cat or not form:
        return out
    if world.paper.get("form_squashed"):
        return out
    if cat.memes.get("sleepy", 0) >= THRESHOLD and form.meters.get("on_bench", 0) >= THRESHOLD:
        world.paper["form_squashed"] = True
        world.fired.add(("sit", "form"))
        out.append("The cat sat on the form so flat it looked like a pancake map.")
    return out


def _r_frustration(world: World) -> list[str]:
    out: list[str] = []
    shopper = world.entities.get("shopper")
    if not shopper:
        return out
    if world.paper.get("frustrated"):
        return out
    if world.paper.get("postcard_chewed") or world.paper.get("form_squashed"):
        world.paper["frustrated"] = True
        shopper.memes["frustration"] = shopper.memes.get("frustration", 0) + 1
        out.append(f"{shopper.id} sighed, because the rebate looked stuck behind two silly troubles.")
    return out


def _r_helper(world: World) -> list[str]:
    out: list[str] = []
    shopper = world.entities.get("shopper")
    merchant = world.entities.get("merchant")
    if not shopper or not merchant:
        return out
    if world.paper.get("helped"):
        return out
    if shopper.memes.get("frustration", 0) >= THRESHOLD:
        world.paper["helped"] = True
        shopper.memes["confidence"] = shopper.memes.get("confidence", 0) + 1
        shopper.memes["frustration"] = max(0.0, shopper.memes.get("frustration", 0) - 1)
        out.append(f"{merchant.label_word.capitalize()} smiled and fetched a fresh form and a new stamp.")
    return out


def _r_paid(world: World) -> list[str]:
    out: list[str] = []
    shopper = world.entities.get("shopper")
    item = world.entities.get("item")
    if not shopper or not item:
        return out
    if world.paper.get("rebate_paid"):
        return out
    if world.paper.get("helped") and world.paper.get("mailed"):
        world.paper["rebate_paid"] = True
        shopper.meters["money_back"] = shopper.meters.get("money_back", 0) + item.meters.get("rebate_amount", 1)
        shopper.memes["joy"] = shopper.memes.get("joy", 0) + 1
        out.append("At last, the rebate was paid, and the shopper got the money back with a laugh.")
    return out


CAUSAL_RULES = [
    Rule("chew", _r_chew),
    Rule("sit", _r_sit),
    Rule("frustration", _r_frustration),
    Rule("helper", _r_helper),
    Rule("paid", _r_paid),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def predict_rebate(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    return {
        "paid": bool(sim.paper.get("rebate_paid")),
        "frustration": sim.get("shopper").memes.get("frustration", 0) if "shopper" in sim.entities else 0,
    }


SHOP = Shop(place="the market")

ITEMS = {
    "kettle": Item(
        id="kettle",
        label="kettle",
        phrase="a sturdy kettle",
        price=12,
        rebate_amount=3,
    ),
    "lamp": Item(
        id="lamp",
        label="lamp",
        phrase="a bright lamp",
        price=20,
        rebate_amount=5,
    ),
    "boots": Item(
        id="boots",
        label="boots",
        phrase="a pair of strong boots",
        price=16,
        rebate_amount=4,
    ),
}

PEOPLE = {
    "grandmother": {"type": "grandmother", "name_pool": ["Mabel", "Agnes", "Nell", "Berta", "June"]},
    "grandfather": {"type": "grandfather", "name_pool": ["Otto", "Hiram", "Silas", "Bram", "Earl"]},
    "aunt": {"type": "aunt", "name_pool": ["Tilda", "Ruth", "Pearl", "Mina", "Dora"]},
}

HELPERS = {
    "merchant": {"type": "merchant", "label": "the merchant"},
    "peddler": {"type": "peddler", "label": "the peddler"},
}

ANIMALS = {
    "goat": {"type": "goat", "label": "the goat"},
    "cat": {"type": "cat", "label": "the cat"},
}

TRAITS = ["careful", "cheerful", "patient", "kind", "witty", "spirited"]


@dataclass
class StoryParams:
    shopper_role: str
    item: str
    helper: str
    name: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A folk-tale storyworld about a rebate, a silly mishap, and a happy ending."
    )
    ap.add_argument("--shopper-role", choices=PEOPLE)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--helper", choices=HELPERS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for role in PEOPLE:
        for item in ITEMS:
            for helper in HELPERS:
                combos.append((role, item, helper))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    role = args.shopper_role or rng.choice(list(PEOPLE))
    item = args.item or rng.choice(list(ITEMS))
    helper = args.helper or rng.choice(list(HELPERS))
    name = args.name or rng.choice(PEOPLE[role]["name_pool"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(shopper_role=role, item=item, helper=helper, name=name, trait=trait)


def make_world(params: StoryParams) -> World:
    world = World(SHOP)
    shopper = world.add(Entity(
        id=params.name,
        kind="character",
        type=PEOPLE[params.shopper_role]["type"],
    ))
    helper = world.add(Entity(
        id="merchant",
        kind="character",
        type=HELPERS[params.helper]["type"],
        label=HELPERS[params.helper]["label"],
    ))
    item_cfg = ITEMS[params.item]
    item = world.add(Entity(
        id="item",
        kind="thing",
        type=item_cfg.id,
        label=item_cfg.label,
        phrase=item_cfg.phrase,
    ))
    goat = world.add(Entity(id="goat", kind="character", type="goat", label="the goat"))
    cat = world.add(Entity(id="cat", kind="character", type="cat", label="the cat"))

    shopper.memes["joy"] = 1
    shopper.memes["hope"] = 1
    goat.memes["mischief"] = 1
    cat.memes["sleepy"] = 1

    world.say(f"Once upon a time, {shopper.id} was a {params.trait} {shopper.type} who loved a fair bargain.")
    world.say(f"One market day, {shopper.id} bought {item.phrase} from {helper.label_word}.")
    world.say(f"{helper.label_word.capitalize()} promised a rebate if the papers were mailed back properly.")
    world.para()
    world.say(f"So {shopper.id} gathered the postcard and the form and walked toward the post box at {SHOP.place}.")
    world.say("But the village had its own ideas about order.")
    world.paper["postcard"] = True
    world.paper["form"] = True
    world.paper["postcard_chewed"] = False
    world.paper["form_squashed"] = False
    world.paper["mailed"] = False

    postcard = world.add(Entity(id="postcard", kind="thing", type="postcard", label="postcard"))
    form = world.add(Entity(id="form", kind="thing", type="form", label="form"))
    postcard.meters["near_goat"] = 1
    form.meters["on_bench"] = 1

    propagate(world, narrate=True)

    if not world.paper.get("helped"):
        world.para()
        world.say(f"{shopper.id} laughed, because the trouble was so tiny and so ridiculous.")
        world.say(f"Then {shopper.id} asked {helper.label_word} for help instead of grumbling.")
        propagate(world, narrate=True)

    world.paper["mailed"] = True
    world.para()
    world.say(f"With the fresh papers and the new stamp, {shopper.id} mailed the rebate at last.")
    propagate(world, narrate=True)
    if world.paper.get("rebate_paid"):
        world.para()
        world.say(f"In the end, {shopper.id} got the rebate back, and the whole village had a good laugh about the goat and the cat.")
        world.say(f"{shopper.id} went home smiling, with the kettle warm again and the money back in a pocket.")

    world.facts.update(
        shopper=shopper,
        helper=helper,
        item=item,
        role=params.shopper_role,
        item_id=params.item,
        helper_id=params.helper,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    shopper = f["shopper"]
    item = f["item"]
    return [
        f'Write a short folk tale about {shopper.id}, a rebate, and {item.phrase}.',
        f"Tell a humorous village story where {shopper.id} tries to claim a rebate for {item.label} after a silly mishap.",
        f'Write a gentle story for children that uses the word "rebate" and ends with a happy laugh.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    shopper = f["shopper"]
    item = f["item"]
    helper = f["helper"]
    qa = [
        QAItem(
            question=f"What did {shopper.id} buy at {SHOP.place}?",
            answer=f"{shopper.id} bought {item.phrase} from {helper.label_word}.",
        ),
        QAItem(
            question=f"What promise did {helper.label_word} make about the purchase?",
            answer=f"{helper.label_word.capitalize()} promised a rebate if the papers were mailed back properly.",
        ),
        QAItem(
            question=f"What silly problem happened to the rebate papers?",
            answer="The goat chewed the postcard and the cat sat on the form.",
        ),
        QAItem(
            question=f"How did {shopper.id} react when the papers got into trouble?",
            answer=f"{shopper.id} laughed, asked for help, and kept going.",
        ),
        QAItem(
            question="What happened at the end of the story?",
            answer=f"The rebate was paid, the money came back, and {shopper.id} went home smiling.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rebate?",
            answer="A rebate is money you get back after you buy something and send in the requested proof or form.",
        ),
        QAItem(
            question="Why do people mail rebate forms?",
            answer="People mail rebate forms so the seller can check the purchase and send back the promised money.",
        ),
        QAItem(
            question="Why can a goat make a story funny?",
            answer="A goat can make a story funny because goats are curious and sometimes nibble things they should not nibble.",
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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for role in PEOPLE:
        lines.append(asp.fact("role", role))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("rebate_amount", item_id, item.rebate_amount))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
    for animal_id in ANIMALS:
        lines.append(asp.fact("animal", animal_id))
    lines.append(asp.fact("requires_mail", "kettle"))
    lines.append(asp.fact("requires_mail", "lamp"))
    lines.append(asp.fact("requires_mail", "boots"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(Role, Item, Helper) :- role(Role), item(Item), helper(Helper).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  paper: {world.paper}")
    return "\n".join(lines)


CURATED = [
    StoryParams("grandmother", "kettle", "merchant", "Mabel", "cheerful"),
    StoryParams("aunt", "lamp", "peddler", "Tilda", "witty"),
    StoryParams("grandfather", "boots", "merchant", "Otto", "patient"),
]


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (role, item, helper) combos:")
        for row in combos:
            print(" ", row)
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
            header = f"### {p.name}: {p.shopper_role} with {p.item} (helper: {p.helper})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
