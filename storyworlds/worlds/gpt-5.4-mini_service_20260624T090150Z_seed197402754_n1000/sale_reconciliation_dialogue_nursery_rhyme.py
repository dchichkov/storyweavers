#!/usr/bin/env python3
"""
Standalone storyworld: sale reconciliation dialogue nursery rhyme.

A tiny classical simulation about a child who wants a toy on sale, a small
misunderstanding with a shopkeeper or parent, and a cheerful reconciliation
through dialogue.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Shop:
    name: str
    rhyme: str
    sale_item: str
    full_price: int
    sale_price: int


@dataclass
class StoryParams:
    shop: str
    item: str
    hero_name: str
    hero_type: str
    helper_type: str
    seed: Optional[int] = None


SHOPS = {
    "toyshop": Shop(name="the toyshop", rhyme="bright and neat", sale_item="toy train", full_price=8, sale_price=5),
    "market": Shop(name="the market stall", rhyme="bustling and sweet", sale_item="basket bunny", full_price=7, sale_price=4),
    "corner": Shop(name="the corner shop", rhyme="small and sweet", sale_item="blue kite", full_price=6, sale_price=3),
}

ITEMS = {
    "toy train": {"label": "toy train", "phrase": "a little toy train", "kind": "toy"},
    "basket bunny": {"label": "basket bunny", "phrase": "a soft basket bunny", "kind": "toy"},
    "blue kite": {"label": "blue kite", "phrase": "a blue kite with a tail", "kind": "toy"},
}

GIRL_NAMES = ["Lily", "Maya", "Nora", "Zoe", "Ella", "Mia"]
BOY_NAMES = ["Leo", "Finn", "Sam", "Ben", "Theo", "Max"]


class World:
    def __init__(self, shop: Shop) -> None:
        self.shop = shop
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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


def rhyme_opening(shop: Shop, item: str) -> str:
    return f"At {shop.name}, {shop.rhyme}, there sat {item} on sale for a little less money."


def reasonableness_gate(shop: Shop, item: str) -> bool:
    return item in ITEMS and shop.sale_price < shop.full_price


def story_setup(world: World, hero: Entity, helper: Entity, item: dict) -> None:
    world.say(f"{hero.id} was a little {hero.type} with a bright idea in {hero.meters.get('heart', 0) or 'heart'} and a wish to buy {item['phrase']}.")
    world.say(f"{helper.pronoun().capitalize()} came along to the {world.shop.name} to help, and the day felt merry and small.")
    world.say(rhyme_opening(world.shop, item["label"]))


def conflict_beats(world: World, hero: Entity, helper: Entity, item: dict) -> None:
    hero.memes["want"] = hero.memes.get("want", 0) + 1
    world.say(f"{hero.id} pointed at {item['label']} and said, 'Oh please, oh please, I want that toy today!'")
    world.say(f"But {helper.pronoun('subject')} shook {helper.pronoun('possessive')} head and said, 'We have to be careful and count the coins all in a row.'")
    world.say(f"{hero.id} looked sad, for {hero.pronoun('subject')} thought the shiny toy might go away before the song was done.")
    hero.memes["sad"] = hero.memes.get("sad", 0) + 1


def reconciliation_dialogue(world: World, hero: Entity, helper: Entity, item: dict) -> None:
    world.say(f"Then {helper.pronoun('subject').capitalize()} sat down and spoke soft and slow: 'Let us talk and look again.'")
    world.say(f"{hero.id} answered, 'If it is on sale, maybe we can choose it together and still be wise.'")
    world.say(f"{helper.pronoun().capitalize()} smiled and said, 'That sounds right to me, dear one. We can make peace with a choice we both can keep.'")
    hero.memes["calm"] = hero.memes.get("calm", 0) + 1
    helper.memes["calm"] = helper.memes.get("calm", 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0) + 1


def resolution(world: World, hero: Entity, helper: Entity, item: dict) -> None:
    world.say(f"So they counted the coins, found the sale price, and bought {item['phrase']} with happy little cheer.")
    world.say(f"{hero.id} carried it home, and the two of them laughed the whole way, no longer cross at all.")
    world.say(f"By bedtime, {hero.id} had {item['label']} on the shelf, and the world felt neat and right.")


def tell(shop: Shop, item_key: str, hero_name: str, hero_type: str, helper_type: str) -> World:
    item = ITEMS[item_key]
    world = World(shop)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="helper"))
    world.facts.update(hero=hero, helper=helper, item=item, shop=shop)

    story_setup(world, hero, helper, item)
    world.para()
    conflict_beats(world, hero, helper, item)
    world.para()
    reconciliation_dialogue(world, hero, helper, item)
    resolution(world, hero, helper, item)
    return world


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny sale-and-reconciliation nursery-rhyme story world.")
    ap.add_argument("--shop", choices=sorted(SHOPS))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
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
    shop = args.shop or rng.choice(sorted(SHOPS))
    item = args.item or rng.choice(sorted(ITEMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    if not reasonableness_gate(SHOPS[shop], item):
        raise StoryError("No valid sale story matches those choices.")
    return StoryParams(shop=shop, item=item, hero_name=name, hero_type=gender, helper_type=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, item, shop = f["hero"], f["helper"], f["item"], f["shop"]
    return [
        f'Write a nursery-rhyme style story about a child named {hero.id}, a sale, and a happy reconciliation.',
        f"Tell a gentle story where {hero.id} wants {item['phrase']} from {shop.name} and {helper.pronoun('subject')} helps them talk it through.",
        f"Write a small story with dialogue in which a sale leads to a misunderstanding and then a cheerful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, item, shop = f["hero"], f["helper"], f["item"], f["shop"]
    return [
        QAItem(
            question=f"What did {hero.id} want at {shop.name}?",
            answer=f"{hero.id} wanted {item['phrase']}, which was on sale.",
        ),
        QAItem(
            question=f"Who helped {hero.id} talk things through?",
            answer=f"{helper.pronoun().capitalize()} helped {hero.id} through a calm conversation.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"The feeling changed from worry to peace, and they bought {item['phrase']} together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean when something is on sale?",
            answer="When something is on sale, it costs less money than it usually does for a little while.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means people make up after a misunderstanding and feel friendly again.",
        ),
        QAItem(
            question="Why do people use dialogue?",
            answer="People use dialogue to talk, share feelings, and understand one another better.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = tell(SHOPS[params.shop], params.item, params.hero_name, params.hero_type, params.helper_type)
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
        print()
        print("--- world model state ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: kind={e.kind} type={e.type} memes={e.memes} meters={e.meters}")
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


ASP_RULES = r"""
shop(S) :- sale_shop(S).
item(I) :- sale_item(I).
valid_story(S, I) :- shop(S), item(I), sale_price(S,P1), full_price(S,P2), P1 < P2.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for key, shop in SHOPS.items():
        lines.append(asp.fact("sale_shop", key))
        lines.append(asp.fact("sale_item", shop.sale_item.replace(" ", "_")))
        lines.append(asp.fact("sale_price", key, shop.sale_price))
        lines.append(asp.fact("full_price", key, shop.full_price))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show valid_story/2.")
    model = asp.one_model(program)
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {(k, v.sale_item.replace(" ", "_")) for k, v in SHOPS.items() if reasonableness_gate(v, v.sale_item)}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    print("clingo:", sorted(clingo_set))
    print("python:", sorted(python_set))
    return 1


def build_all() -> list[StoryParams]:
    out = []
    for shop in sorted(SHOPS):
        for item in sorted(ITEMS):
            if reasonableness_gate(SHOPS[shop], item):
                out.append(StoryParams(shop=shop, item=item, hero_name="Lily", hero_type="girl", helper_type="mother"))
    return out


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in build_all():
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
