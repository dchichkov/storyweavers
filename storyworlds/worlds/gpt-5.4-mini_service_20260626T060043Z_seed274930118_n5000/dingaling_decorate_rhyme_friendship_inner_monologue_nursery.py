#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about a dingaling, a decorating wish, and a
friendship fix.

Seed tale imagined from the prompt:
---
A little lamb named Nell hears a dingaling on a bicycle and wants to decorate it
with bright ribbons and stickers. Her friend Pip worries the bell will stop
ringing clearly. Nell's inner monologue wobbles between wanting it pretty and
wanting it useful. In the end they decorate a paper tag and a basket instead,
keeping the dingaling bright and the friendship bright too.
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "sheep", "lamb"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    location: str
    fragile_sound: bool = False
    decorate_targets: set[str] = field(default_factory=set)


@dataclass
class Offer:
    id: str
    label: str
    phrase: str
    safe_targets: set[str]
    prep: str
    tail: str


@dataclass
class StoryParams:
    setting: str
    wish_item: str
    decoration: str
    name: str
    friend_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "garden": "the garden",
    "playroom": "the playroom",
    "yard": "the yard",
}

ITEMS = {
    "dingaling": Item(
        id="dingaling",
        label="dingaling",
        phrase="a little shiny bell",
        location="handlebar",
        fragile_sound=True,
        decorate_targets={"tag", "basket"},
    ),
    "kite": Item(
        id="kite",
        label="kite",
        phrase="a bright kite string",
        location="string",
        fragile_sound=False,
        decorate_targets={"tail", "string"},
    ),
}

DECORATIONS = {
    "ribbon": "ribbons",
    "sticker": "stickers",
    "paint": "paint",
    "flower": "paper flowers",
}

SAFE_DECORATIONS = {
    "tag": Offer(
        id="tag",
        label="paper tag",
        phrase="a paper tag with a bow",
        safe_targets={"ribbon", "sticker", "paint", "flower"},
        prep="decorate the paper tag instead",
        tail="tied the pretty tag to the handlebar",
    ),
    "basket": Offer(
        id="basket",
        label="basket",
        phrase="a small basket",
        safe_targets={"ribbon", "sticker", "flower"},
        prep="decorate the basket instead",
        tail="tucked the ribbons into the basket",
    ),
}

CHARACTER_NAMES = ["Nell", "Pip", "Mia", "Tom", "Luna", "Bea"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A wish is risky when the child wants to decorate the sound-making dingaling.
risky(W) :- item(W), fragile_sound(W), wants_decorate(W).

% A safe offer exists when there is some other target that can hold the decorations.
safe_offer(W, O) :- risky(W), offer(O), safe_for(O, W).

valid_story(S, W, D) :- setting(S), item(W), decoration(D), risky(W), safe_decoration(D, W).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.fragile_sound:
            lines.append(asp.fact("fragile_sound", iid))
        for tgt in item.decorate_targets:
            lines.append(asp.fact("safe_decoration", tgt, iid))
    for did in DECORATIONS:
        lines.append(asp.fact("decoration", did))
        if did == "ribbon":
            lines.append(asp.fact("wants_decorate", "dingaling"))
    for oid, offer in SAFE_DECORATIONS.items():
        lines.append(asp.fact("offer", oid))
        for tgt in offer.safe_targets:
            lines.append(asp.fact("safe_for", oid, "dingaling"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show risky/1.\n#show valid_story/3."))
    shown = set(asp.atoms(model, "risky"))
    python = {("dingaling",)} if should_warn(ITEMS["dingaling"]) else set()
    if shown == python:
        print("OK: clingo gate matches Python gate.")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("clingo:", sorted(shown))
    print("python:", sorted(python))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def should_warn(item: Item) -> bool:
    return item.fragile_sound


def pick_safe_offer(item: Item, decoration: str) -> Optional[Offer]:
    if decoration not in {"ribbon", "sticker", "flower"}:
        return None
    if item.id != "dingaling":
        return None
    return SAFE_DECORATIONS["tag"] if decoration in {"sticker", "paint"} else SAFE_DECORATIONS["basket"]


def render_setting(setting: str) -> str:
    return {
        "garden": "The garden was green and low and still.",
        "playroom": "The playroom was cozy and bright as a toy-box dream.",
        "yard": "The yard was round with grass and a little path.",
    }[setting]


def tell(world: World, hero: Entity, friend: Entity, item: Entity, decoration: str) -> None:
    world.say(
        f"{hero.id} was a little lamb with a heart so spry, and {friend.id} was a friend who stayed nearby."
    )
    world.say(
        f"One day {hero.id} heard a dingaling on {item.phrase} and wished to decorate it with {DECORATIONS[decoration]}."
    )
    world.say(
        f"{hero.id} loved bright things, and {hero.pronoun('possessive')} little inner monologue twinkled: "
        f'"Pretty and merry, shiny and cheery!"'
    )
    world.para()
    world.say(render_setting(world.setting))
    world.say(
        f"But {friend.id} said, \"If we cover the dingaling, it may not sing so clear on the windy swing.\""
    )
    world.say(
        f"That made {hero.id} pause and think: {hero.pronoun().capitalize()} wanted it lovely, but {hero.pronoun('possessive')} friend was right to worry."
    )
    hero.memes["worry"] = 1.0
    hero.memes["desire"] = 1.0
    friend.memes["care"] = 1.0
    world.para()

    offer = pick_safe_offer(item, decoration)
    if not offer:
        raise StoryError("No safe decorating choice fits this wish.")
    world.say(
        f"So {hero.id} and {friend.id} chose to {offer.prep}, while the dingaling stayed bare and bright."
    )
    world.say(
        f"They {offer.tail}, and the bell still rang ding-ding with a happy ring."
    )
    world.say(
        f"{hero.id} smiled at the shine, and {friend.id} smiled too, because the friendship stayed fine."
    )

    hero.memes["joy"] = 1.0
    hero.memes["worry"] = 0.0
    friend.memes["joy"] = 1.0
    item.meters["bright"] = 1.0
    item.meters["quiet_damage"] = 0.0
    world.facts.update(hero=hero, friend=friend, item=item, decoration=decoration, offer=offer)


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short nursery-rhyme style story about a dingaling and a child who wants to decorate it.',
        f"Tell a gentle story where {f['hero'].id} wants to decorate a dingaling but a friend worries about the bell's sound.",
        "Write a small friendship story with an inner monologue, a choice, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    item: Entity = f["item"]
    offer: Offer = f["offer"]
    decoration = f["decoration"]

    return [
        QAItem(
            question=f"What did {hero.id} want to do to the dingaling?",
            answer=f"{hero.id} wanted to decorate the dingaling with {DECORATIONS[decoration]}.",
        ),
        QAItem(
            question=f"Why did {friend.id} worry about the dingaling?",
            answer=f"{friend.id} worried that covering the dingaling might make it stop ringing clearly.",
        ),
        QAItem(
            question=f"What did they decorate instead?",
            answer=f"They decorated the {offer.label} instead and left the dingaling bright and able to ring.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy, because the choice was pretty and safe and the friendship stayed strong.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a bell do?",
            answer="A bell makes a ringing sound when you move it or strike it.",
        ),
        QAItem(
            question="What are ribbons used for?",
            answer="Ribbons can be used to tie things up or make them look pretty.",
        ),
        QAItem(
            question="What is a friend?",
            answer="A friend is someone who cares about you, helps you, and plays with you.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet talking a person does inside their own mind.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="garden", wish_item="dingaling", decoration="ribbon", name="Nell", friend_name="Pip"),
    StoryParams(setting="playroom", wish_item="dingaling", decoration="sticker", name="Mia", friend_name="Bea"),
    StoryParams(setting="yard", wish_item="dingaling", decoration="flower", name="Luna", friend_name="Tom"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: dingaling, decorate, friendship, inner monologue.")
    ap.add_argument("--setting", choices=list(SETTINGS))
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--decoration", choices=list(DECORATIONS))
    ap.add_argument("--item", choices=list(ITEMS))
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
    setting = args.setting or rng.choice(list(SETTINGS))
    item = args.item or "dingaling"
    decoration = args.decoration or rng.choice(list(DECORATIONS))
    if item != "dingaling":
        raise StoryError("This tiny world only tells the dingaling story.")
    if decoration == "paint":
        raise StoryError("Painting the dingaling is not the safe rhyme for this world.")
    name = args.name or rng.choice(CHARACTER_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in CHARACTER_NAMES if n != name])
    return StoryParams(setting=setting, wish_item=item, decoration=decoration, name=name, friend_name=friend_name)


def generate(params: StoryParams) -> StorySample:
    world = World(setting=SETTINGS[params.setting])
    hero = world.add(Entity(id=params.name, kind="character", type="lamb"))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="friend"))
    item = world.add(Entity(id=params.wish_item, kind="thing", type="bell", label="dingaling", phrase="the little bell"))

    tell(world, hero, friend, item, params.decoration)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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
        print(asp_program("#show risky/1.\n#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show risky/1.\n#show valid_story/3."))
        print("risky:", asp.atoms(model, "risky"))
        print("valid_story:", asp.atoms(model, "valid_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
