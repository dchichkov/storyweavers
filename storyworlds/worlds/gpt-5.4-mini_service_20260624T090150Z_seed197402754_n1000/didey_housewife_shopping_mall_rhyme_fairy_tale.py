#!/usr/bin/env python3
"""
storyworlds/worlds/didey_housewife_shopping_mall_rhyme_fairy_tale.py
====================================================================

A small story world for a fairy-tale shopping-mall rhyme.

Seed idea:
- Didey goes with a housewife to a shopping mall.
- Didey wants a shiny toy / sweet treat.
- The housewife worries about their coins.
- They find a gentle compromise using a coupon, a tiny gift, and kind words.

The world keeps the prose state-driven: the story changes because the budget,
the wish, and the compromise change the characters' emotional meters.

This world includes:
- didey
- housewife
- shopping mall
- rhyme
- fairy-tale tone
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "mother", "housewife", "woman"}
        masculine = {"boy", "father", "man"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the shopping mall"
    affords: set[str] = field(default_factory=set)


@dataclass
class Wish:
    id: str
    item: str
    phrase: str
    price: int
    sparkle: str
    reply_rhyme: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Deal:
    id: str
    label: str
    prep: str
    tail: str
    discount: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "mall": Setting(place="the shopping mall", affords={"browse", "buy", "snack"}),
}

WISHES = {
    "glass_slipper": Wish(
        id="glass_slipper",
        item="glass slippers",
        phrase="a pair of glass slippers with silver bows",
        price=8,
        sparkle="sparkled like moonlight",
        reply_rhyme="shine / mine",
        tags={"shiny", "fairy_tale"},
    ),
    "music_box": Wish(
        id="music_box",
        item="music box",
        phrase="a tiny music box that played a sweet tune",
        price=6,
        sparkle="glimmered like a candle flame",
        reply_rhyme="song / long",
        tags={"music", "fairy_tale"},
    ),
    "red_cape": Wish(
        id="red_cape",
        item="red cape",
        phrase="a little red cape with a gold clasp",
        price=5,
        sparkle="fluttered like a bright banner",
        reply_rhyme="cape / shape",
        tags={"cloth", "fairy_tale"},
    ),
}

DEALS = {
    "coupon": Deal(
        id="coupon",
        label="a lucky coupon",
        prep="use the coupon",
        tail="paid less at the little shop",
        discount=3,
        tags={"money"},
    ),
    "single_treat": Deal(
        id="single_treat",
        label="one small treat",
        prep="choose one small treat instead",
        tail="picked a tiny gift and saved the rest",
        discount=4,
        tags={"money", "snack"},
    ),
    "window_song": Deal(
        id="window_song",
        label="a window-shop song",
        prep="sing a little window-shop song and look carefully",
        tail="left with happy hearts and full hands",
        discount=0,
        tags={"song"},
    ),
}

GIRL_NAMES = ["Didey", "Mina", "Lina", "Suri", "Taya"]
BOY_NAMES = ["Didey", "Nico", "Ari", "Pip", "Rafi"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    wish: str
    deal: str
    name: str = "Didey"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
wish_risk(W) :- wish(W), price(W, P), budget(B), P > B.
deal_helps(D, W) :- deal(D), wish_risk(W), discount(D, X), price(W, P), budget(B), P - X =< B.
valid_story(Place, Wish, Deal) :- setting(Place), wish(Wish), deal(Deal), deal_helps(Deal, Wish).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "mall"))
    lines.append(asp.fact("budget", 5))
    for wid, w in WISHES.items():
        lines.append(asp.fact("wish", wid))
        lines.append(asp.fact("price", wid, w.price))
    for did, d in DEALS.items():
        lines.append(asp.fact("deal", did))
        lines.append(asp.fact("discount", did, d.discount))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = set(valid_stories())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_stories() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python valid stories:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_stories() -> list[tuple[str, str, str]]:
    combos = []
    budget = 5
    for place in SETTINGS:
        for wish_id, wish in WISHES.items():
            if wish.price <= budget:
                continue
            for deal_id, deal in DEALS.items():
                if wish.price - deal.discount <= budget:
                    combos.append((place, wish_id, deal_id))
    return combos


def explain_rejection(wish: Wish, deal: Deal) -> str:
    return (
        f"(No story: {wish.item} costs too much for the little purse even after "
        f"{deal.label}. Try a pricier wish or a stronger bargain.)"
    )


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def rhyme_line(a: str, b: str) -> str:
    return f"{a} / {b}"


def tell(setting: Setting, wish: Wish, deal: Deal, name: str = "Didey") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=name,
        kind="character",
        type="girl",
        traits=["small", "bright", "hopeful"],
        meters={"coins": 5},
        memes={"wish": 0.0, "worry": 0.0, "joy": 0.0},
    ))
    housewife = world.add(Entity(
        id="Housewife",
        kind="character",
        type="housewife",
        label="the housewife",
        traits=["kind", "careful"],
        meters={"coins": 5},
        memes={"worry": 0.0, "joy": 0.0},
    ))
    treasure = world.add(Entity(
        id=wish.id,
        type="thing",
        label=wish.item,
        phrase=wish.phrase,
        owner=hero.id,
        caretaker=housewife.id,
        meters={"price": wish.price},
    ))

    # Act 1
    world.say(
        f"Once in the shine of the shopping mall, little {hero.id} walked with "
        f"{hero.pronoun('possessive')} housewife, and the bright floors gleamed "
        f"like a storybook hall."
    )
    world.say(
        f"{hero.id} saw {treasure.phrase}; it {wish.sparkle}, and the wish in "
        f"{hero.pronoun('possessive')} chest began to call."
    )
    hero.memes["wish"] += 1

    # Act 2
    world.para()
    world.say(
        f"{hero.id} said, '{wish.reply_rhyme.split(" / ")[0].capitalize()}! {wish.reply_rhyme.split(" / ")[1]}!' "
        f"and reached with eager hands, but {hero.pronoun('possessive')} housewife "
        f"counted the coins and frowned a little in fear."
    )
    housewife.memes["worry"] += 1
    if wish.price > hero.meters["coins"]:
        world.say(
            f'"If we buy that now," said the housewife, "the purse will feel light '
            f"as a leaf, and there may be no silver left for the year."'
        )
    world.say(
        f"{hero.id} pouted, for the little wish felt close enough to touch, yet "
        f"far enough to stir a tear."
    )

    # Act 3
    world.para()
    world.say(
        f"Then the housewife spotted {deal.label} near the checkout, and the sign "
        f"winked like a star."
    )
    if wish.price - deal.discount > hero.meters["coins"]:
        raise StoryError("The chosen deal does not actually make the wish affordable.")

    hero.meters["coins"] -= max(0, wish.price - deal.discount)
    housewife.meters["coins"] -= max(0, wish.price - deal.discount)
    hero.memes["worry"] = 0.0
    hero.memes["joy"] += 1
    housewife.memes["worry"] = 0.0
    housewife.memes["joy"] += 1

    world.say(
        f'"How about we {deal.prep}?" the housewife asked, soft as a lullaby.'
    )
    world.say(
        f"{hero.id}'s eyes lit up. '{wish.reply_rhyme.split(" / ")[0].capitalize()} "
        f"{wish.reply_rhyme.split(" / ")[1]}, yes please!' {hero.id} sang, and "
        f"they {deal.tail}."
    )
    world.say(
        f"In the end, {hero.id} carried {treasure.it()} home at last, and the housewife "
        f"smiled at the tidy purse and the happy heart within it."
    )

    world.facts.update(hero=hero, housewife=housewife, wish=wish, deal=deal, setting=setting)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    wish: Wish = f["wish"]
    return [
        f'Write a short fairy-tale rhyme set in the shopping mall that includes "{wish.item}".',
        f"Tell a gentle story about Didey and a housewife who disagree over {wish.phrase} and then find a kind bargain.",
        f'Write a child-friendly rhyming tale where a wish seems too costly, but a coupon or small treat saves the day.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    wish: Wish = f["wish"]
    deal: Deal = f["deal"]
    housewife: Entity = f["housewife"]
    return [
        QAItem(
            question=f"Who wanted {wish.phrase} at the shopping mall?",
            answer=f"{hero.id} wanted {wish.phrase} while walking with {hero.pronoun('possessive')} housewife.",
        ),
        QAItem(
            question=f"Why did the housewife worry about buying {wish.item}?",
            answer=(
                f"The housewife worried because {wish.item} cost too much for the purse, "
                f"and she wanted to keep enough coins for later."
            ),
        ),
        QAItem(
            question=f"How did they make {wish.item} possible in the end?",
            answer=(
                f"They used {deal.label} and chose a cheaper way, so {hero.id} could "
                f"bring {wish.item} home without breaking the little budget."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shopping mall?",
            answer="A shopping mall is a big building with many stores, where people can walk around, shop, and buy things.",
        ),
        QAItem(
            question="What does a coupon do?",
            answer="A coupon is a small paper or code that helps people pay less money for something they want to buy.",
        ),
        QAItem(
            question="What is a bargain?",
            answer="A bargain is something you can buy for a lower price than usual, which helps save coins or money.",
        ),
    ]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale rhyme storyworld set in a shopping mall.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--wish", choices=WISHES.keys())
    ap.add_argument("--deal", choices=DEALS.keys())
    ap.add_argument("--name")
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
    if args.wish and args.deal:
        wish = WISHES[args.wish]
        deal = DEALS[args.deal]
        if wish.price - deal.discount > 5:
            raise StoryError(explain_rejection(wish, deal))
    combos = [c for c in valid_stories()
              if (args.place is None or c[0] == args.place)
              and (args.wish is None or c[1] == args.wish)
              and (args.deal is None or c[2] == args.deal)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, wish_id, deal_id = rng.choice(sorted(combos))
    name = args.name or "Didey"
    return StoryParams(place=place, wish=wish_id, deal=deal_id, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], WISHES[params.wish], DEALS[params.deal], params.name)
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
    StoryParams(place="mall", wish="glass_slipper", deal="coupon", name="Didey"),
    StoryParams(place="mall", wish="music_box", deal="single_treat", name="Didey"),
    StoryParams(place="mall", wish="red_cape", deal="window_song", name="Didey"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible story combos:\n")
        for place, wish, deal in combos:
            print(f"  {place:10} {wish:14} {deal}")
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
            header = f"### {p.name}: {p.wish} via {p.deal}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
