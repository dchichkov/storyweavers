#!/usr/bin/env python3
"""
storyworlds/worlds/daisy_merchant_batter_surprise_heartwarming.py
==================================================================

A small heartwarming storyworld about a daisy-loving child, a friendly merchant,
and a surprise batter for a shared treat.

Premise:
- A child named Daisy wants to help at a little market stall.
- A merchant has batter for pancakes.
- A surprise gift or gesture turns a small mix-up into a warm, happy ending.

The world is intentionally compact: the main tension is about whether there is
enough batter and whether the surprise will work, and the resolution is a
kind, concrete change in the physical and emotional state of the world.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

@dataclass
class Setting:
    place: str
    indoors: bool = False


@dataclass
class ActorSpec:
    name: str
    type: str
    trait: str


@dataclass
class MerchantSpec:
    name: str
    type: str = "merchant"
    trait: str = "kind"


@dataclass
class BatterSpec:
    label: str
    phrase: str
    flavor: str
    amount: int
    surprise_kind: str


SETTINGS = {
    "market": Setting(place="the little market", indoors=False),
    "kitchen": Setting(place="the warm kitchen", indoors=True),
    "bakery": Setting(place="the bakery corner", indoors=True),
}

ACTORS = [
    ActorSpec(name="Daisy", type="girl", trait="gentle"),
    ActorSpec(name="Mina", type="girl", trait="helpful"),
    ActorSpec(name="Lila", type="girl", trait="curious"),
]

MERCHANTS = [
    MerchantSpec(name="Mara"),
    MerchantSpec(name="Nico", trait="cheerful"),
    MerchantSpec(name="Tess", trait="friendly"),
]

BATTERS = {
    "pancake": BatterSpec(
        label="batter",
        phrase="a bowl of pancake batter",
        flavor="sweet",
        amount=2,
        surprise_kind="butterflower",
    ),
    "blueberry": BatterSpec(
        label="batter",
        phrase="a bowl of blueberry batter",
        flavor="fruity",
        amount=2,
        surprise_kind="blueberry smile",
    ),
    "cookie": BatterSpec(
        label="batter",
        phrase="a thick bowl of cookie batter",
        flavor="sweet",
        amount=2,
        surprise_kind="tiny star sprinkles",
    ),
}

SURPRISES = {
    "flowers": "a daisy on top",
    "note": "a note that said 'For you, with thanks.'",
    "gift": "a ribbon-tied little gift",
}

TRADE_ITEMS = {
    "coin": "a shiny coin",
    "daisy": "a paper daisy",
    "help": "a helping hand",
}


# ---------------------------------------------------------------------------
# Params and live story
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    actor: str
    merchant: str
    batter: str
    surprise: str
    trade: str
    seed: Optional[int] = None


def _choose(rng: random.Random, items):
    return rng.choice(list(items))


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------

def batter_can_support_surprise(batter: BatterSpec, surprise: str) -> bool:
    return surprise in SURPRISES and batter.amount >= 1


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for actor in ACTORS:
            for merchant in MERCHANTS:
                for batter in BATTERS:
                    for surprise in SURPRISES:
                        if batter_can_support_surprise(BATTERS[batter], surprise):
                            combos.append((setting, actor.name, merchant.name, batter, surprise))
    return combos


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    actor_spec = next(a for a in ACTORS if a.name == params.actor)
    merchant_spec = next(m for m in MERCHANTS if m.name == params.merchant)
    batter_spec = BATTERS[params.batter]
    surprise_text = SURPRISES[params.surprise]

    actor = world.add(Entity(
        id="actor",
        kind="character",
        type=actor_spec.type,
        label=actor_spec.name,
        memes={"joy": 0.0, "hope": 0.0, "surprise": 0.0, "love": 0.0},
    ))
    merchant = world.add(Entity(
        id="merchant",
        kind="character",
        type="merchant",
        label=merchant_spec.name,
        memes={"calm": 0.0, "warmth": 0.0, "gratitude": 0.0},
    ))
    batter = world.add(Entity(
        id="batter",
        kind="thing",
        type="batter",
        label="batter",
        phrase=batter_spec.phrase,
        caretaker=merchant.id,
        meters={"amount": float(batter_spec.amount)},
        memes={"sweetness": 1.0},
    ))
    surprise = world.add(Entity(
        id="surprise",
        kind="thing",
        type="surprise",
        label="surprise",
        phrase=surprise_text,
        owner=actor.id,
        memes={"delight": 0.0},
    ))

    # Facts for QA
    world.facts.update(
        setting=setting,
        actor=actor,
        merchant=merchant,
        batter=batter,
        surprise=surprise,
        batter_spec=batter_spec,
        actor_spec=actor_spec,
        merchant_spec=merchant_spec,
    )

    # Act 1: setup
    world.say(
        f"{actor.label} loved {setting.place} because it always felt bright and friendly."
    )
    world.say(
        f"At a small table, {merchant.label} was stirring {batter.phrase} and smiling at everyone who passed."
    )
    world.say(
        f"{actor.label} noticed the batter and wanted to help."
    )

    # Act 2: tension
    world.para()
    actor.memes["hope"] += 1
    world.say(
        f"{actor.label} asked if there was enough batter for one more treat."
    )
    if batter.meters["amount"] < 2:
        world.say(
            f"{merchant.label} looked worried because the bowl was nearly empty."
        )
    else:
        world.say(
            f"{merchant.label} paused, because the bowl was almost ready to be shared."
        )

    # Surprise turn
    world.say(
        f"Then {actor.label} tucked in {TRADE_ITEMS[params.trade]} and offered it with a shy grin."
    )
    actor.memes["surprise"] += 1
    merchant.memes["warmth"] += 1

    # Act 3: resolution
    world.para()
    if params.surprise == "flowers":
        world.say(
            f"{merchant.label} laughed softly and placed a tiny daisy on top of the finished treat."
        )
    elif params.surprise == "note":
        world.say(
            f"{merchant.label} found the note and smiled so warmly that the whole table seemed to glow."
        )
    else:
        world.say(
            f"{merchant.label} tied the little gift beside the bowl and said it made the day feel extra kind."
        )

    batter.meters["amount"] = 0.0
    actor.memes["joy"] += 1
    actor.memes["love"] += 1
    merchant.memes["gratitude"] += 1
    surprise.memes["delight"] += 1

    world.say(
        f"Together they shared the last of the batter as a fresh treat, and {actor.label} left with a full heart."
    )
    return world


# ---------------------------------------------------------------------------
# Narration
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    actor = f["actor"]
    merchant = f["merchant"]
    batter = f["batter"]
    return [
        f"Write a heartwarming story about {actor.label}, a merchant, and some batter with a surprise at the end.",
        f"Tell a gentle children's story where {actor.label} helps {merchant.label} with {batter.phrase} and everyone feels happy.",
        "Write a short story that begins at a small market, includes batter, and ends with a kind surprise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    actor = f["actor"]
    merchant = f["merchant"]
    batter = f["batter"]
    return [
        QAItem(
            question=f"Who wanted to help at the market?",
            answer=f"{actor.label} wanted to help at the market.",
        ),
        QAItem(
            question=f"What was {merchant.label} stirring?",
            answer=f"{merchant.label} was stirring {batter.phrase}.",
        ),
        QAItem(
            question=f"What made the ending feel special?",
            answer=f"The surprise made the ending feel special, and it turned the little worry about the batter into a warm happy moment.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is batter?",
            answer="Batter is a smooth mixture used for cooking things like pancakes or cakes before it is baked or fried.",
        ),
        QAItem(
            question="What is a merchant?",
            answer="A merchant is a person who sells things or trades goods with other people.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that can make someone feel amazed, happy, or curious.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(S) :- place(S).
actor(A) :- person(A).
merchant(M) :- person(M), is_merchant(M).
batter(B) :- thing(B), batter_kind(B).
surprise(X) :- thing(X), surprise_kind(X).

supports_surprise(B, X) :- batter(B), surprise(X), amount(B, N), N >= 1.
valid_story(S, A, M, B, X) :- setting(S), actor(A), merchant(M), batter(B), surprise(X), supports_surprise(B, X).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for key in SETTINGS:
        lines.append(asp.fact("place", key))
    for a in ACTORS:
        lines.append(asp.fact("person", a.name))
    for m in MERCHANTS:
        lines.append(asp.fact("person", m.name))
        lines.append(asp.fact("is_merchant", m.name))
    for key, b in BATTERS.items():
        lines.append(asp.fact("thing", key))
        lines.append(asp.fact("batter_kind", key))
        lines.append(asp.fact("amount", key, b.amount))
    for key in SURPRISES:
        lines.append(asp.fact("thing", key))
        lines.append(asp.fact("surprise_kind", key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    # Minimal parity check: ASP must produce at least the same shape of valid combos.
    py = set(valid_combos())
    asp_model = asp.one_model(asp_program("#show valid_story/5."))
    asp_set = set(asp.atoms(asp_model, "valid_story"))
    if len(asp_set) == len(py):
        print(f"OK: ASP produced {len(asp_set)} candidate stories.")
        return 0
    print("MISMATCH between ASP and Python candidate counts.")
    print(f"Python: {len(py)}")
    print(f"ASP: {len(asp_set)}")
    return 1


# ---------------------------------------------------------------------------
# Story API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming story world with Daisy, a merchant, batter, and a surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--actor", choices=[a.name for a in ACTORS])
    ap.add_argument("--merchant", choices=[m.name for m in MERCHANTS])
    ap.add_argument("--batter", choices=BATTERS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--trade", choices=TRADE_ITEMS)
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
    setting = args.setting or _choose(rng, SETTINGS.keys())
    actor = args.actor or _choose(rng, [a.name for a in ACTORS])
    merchant = args.merchant or _choose(rng, [m.name for m in MERCHANTS])
    batter = args.batter or _choose(rng, BATTERS.keys())
    surprise = args.surprise or _choose(rng, SURPRISES.keys())
    trade = args.trade or _choose(rng, TRADE_ITEMS.keys())

    if batter not in BATTERS:
        raise StoryError("Unknown batter.")
    if not batter_can_support_surprise(BATTERS[batter], surprise):
        raise StoryError("That batter cannot support the requested surprise.")

    return StoryParams(
        setting=setting,
        actor=actor,
        merchant=merchant,
        batter=batter,
        surprise=surprise,
        trade=trade,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/5."))
        items = sorted(set(asp.atoms(model, "valid_story")))
        for item in items:
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(setting="market", actor="Daisy", merchant="Mara", batter="pancake", surprise="flowers", trade="daisy"),
            StoryParams(setting="kitchen", actor="Mina", merchant="Nico", batter="blueberry", surprise="note", trade="help"),
            StoryParams(setting="bakery", actor="Lila", merchant="Tess", batter="cookie", surprise="gift", trade="coin"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
            header = f"### {p.actor} at {p.setting} with {p.batter} and {p.surprise}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
