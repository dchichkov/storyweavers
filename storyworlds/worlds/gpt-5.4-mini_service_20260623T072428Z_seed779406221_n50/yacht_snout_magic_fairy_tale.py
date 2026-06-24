#!/usr/bin/env python3
"""
storyworlds/worlds/yacht_snout_magic_fairy_tale.py
===================================================

A small fairy-tale storyworld about a yacht, a snout, and a little magic.

Seed tale sketch:
---
Once upon a time, a tiny fairy named Pippa lived near a bright blue harbor.
She loved magic, sparkles, and helping boats. One morning, a proud yacht
named Pearl needed a shiny golden figurehead for the festival sail.

A cranky sea lion with a muddy snout had bumped the yacht and left the bow
all dull and gray. Pippa wanted to fix it with a magic charm, but the harbor
wizard warned that only a kind spell would stick. Pippa listened, mixed a
gentle spell with a drop of moonlight, and the yacht's snout-shaped figurehead
glowed gold again.

The yacht sailed off sparkling, and the sea lion even got a splash of kindness
and a clean nose.

This script turns that seed into a small, constraint-checked simulation with
typed entities, physical meters, emotional memes, a tiny ASP twin, and story-
driven prose.
"""

from __future__ import annotations

import argparse
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: str = ""
    caretaker: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    traits: list[str] = field(default_factory=list)
    magical: bool = False
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "fairy", "woman", "queen"}
        male = {"boy", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    harbor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Spell:
    id: str
    label: str
    phrase: str
    requires_kindness: bool = True
    clean_effect: str = "glow"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    owner_kind: str = "boat"
    magical: bool = False
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def _r_magic(world: World) -> list[str]:
    out: list[str] = []
    fairy = world.entities.get("Pippa")
    snout = world.entities.get("Snout")
    yacht = world.entities.get("Yacht")
    if not fairy or not snout or not yacht:
        return out
    if fairy.memes["kindness"] < THRESHOLD or fairy.memes["spell"] < THRESHOLD:
        return out
    sig = ("magic_clean",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if snout.meters["mud"] >= THRESHOLD:
        snout.meters["mud"] = 0.0
        snout.meters["clean"] += 1
        yacht.meters["shine"] += 1
        fairy.memes["joy"] += 1
        out.append("__magic__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        sents = _r_magic(world)
        if sents:
            changed = True
            produced.extend(s for s in sents if s != "__magic__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combo(place: Place, spell: Spell, prize: Prize) -> bool:
    return place.harbor and "magic" in place.affords and spell.requires_kindness and prize.magical


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for sid, spell in SPELLS.items():
            for tid, prize in PRIZES.items():
                if valid_combo(place, spell, prize):
                    out.append((pid, sid, tid))
    return out


@dataclass
class StoryParams:
    place: str
    spell: str
    prize: str
    fairy: str
    snout_owner: str
    seed: Optional[int] = None


PLACES = {
    "harbor": Place(id="harbor", label="the harbor", harbor=True, affords={"magic"}),
    "bay": Place(id="bay", label="the bay", harbor=True, affords={"magic"}),
}

SPELLS = {
    "moon_dust": Spell(id="moon_dust", label="moon-dust spell", phrase="a moon-dust charm", tags={"magic"}),
    "kind_breeze": Spell(id="kind_breeze", label="kind-breeze spell", phrase="a kind-breeze charm", tags={"magic"}),
}

PRIZES = {
    "figurehead": Prize(
        id="figurehead",
        label="figurehead",
        phrase="a snout-shaped figurehead",
        region="bow",
        magical=True,
        tags={"yacht", "snout"},
    ),
    "snout": Prize(
        id="snout",
        label="snout",
        phrase="a golden snout ornament",
        region="bow",
        magical=True,
        tags={"snout"},
    ),
}

FAIRY_NAMES = ["Pippa", "Luna", "Miri", "Tess"]
SNUFFY_NAMES = ["Seal", "Otter", "Sea Lion", "Walrus"]
TRAITS = ["gentle", "bright", "curious", "cheerful"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale yacht-and-snout storyworld with magic.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--snout-owner")
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
              if (args.place is None or c[0] == args.place)
              and (args.spell is None or c[1] == args.spell)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, spell, prize = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        spell=spell,
        prize=prize,
        fairy=args.name or rng.choice(FAIRY_NAMES),
        snout_owner=args.snout_owner or rng.choice(SNUFFY_NAMES),
    )


def tell(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    fairy = world.add(Entity(id=params.fairy, kind="character", type="fairy", magical=True))
    yacht = world.add(Entity(id="Yacht", kind="character", type="boat", label="the yacht", magical=False))
    snout = world.add(Entity(id="Snout", kind="character", type="animal", label=params.prize))
    owner = world.add(Entity(id="SnoutOwner", kind="character", type="animal", label=params.snout_owner))
    spell = SPELLS[params.spell]
    prize = PRIZES[params.prize]

    fairy.memes["love_magic"] += 1
    fairy.memes["kindness"] += 1
    yacht.meters["dull"] += 1
    snout.meters["mud"] += 1
    snout.memes["grumpy"] += 1

    world.say(f"Once upon a time, {fairy.id} lived beside {world.place.label}.")
    world.say(f"She loved magic, and she loved the proud yacht called {yacht.id}.")
    world.say(f"One morning, {owner.label_word if hasattr(owner, 'label_word') else owner.id} had muddied the yacht's bow, and the {prize.label} looked gray.")
    world.para()
    world.say(f"{fairy.id} wanted to use {spell.phrase} to make {prize.phrase} shine again, but she knew a spell had to be kind.")
    fairy.memes["spell"] += 1
    world.say(f"The snout near the bow was still messy, and everyone could see the need for a gentle fix.")
    world.para()
    if prize.magical and world.place.harbor:
        if spell.requires_kindness:
            world.say(f"{fairy.id} whispered the {spell.label}, and moonlight gathered on the {prize.label}.")
            snout.meters["mud"] = 0.0
            snout.meters["clean"] += 1
            yacht.meters["shine"] += 1
            fairy.memes["joy"] += 1
            world.say(f"The {prize.label} glowed gold again, and the yacht looked ready for the festival sail.")
            world.say(f"{owner.id} blinked, touched {snout.it()} gently, and even the grumpy snout looked glad to be clean.")
        else:
            world.say(f"The spell wobbled, the harbor stayed dim, and the yacht still needed help.")
    world.para()
    world.say(f"In the end, {yacht.id} sailed off sparkling while {fairy.id} waved from the dock.")
    world.say(f"The little snout was clean, the magic was kind, and the fairy tale ended with a bright bow.")
    world.facts.update(fairy=fairy, yacht=yacht, snout=snout, owner=owner, spell=spell, prize=prize, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short fairy tale about a yacht, a snout, and a kind magic spell.',
        f"Tell a gentle story where {world.facts['fairy'].id} uses magic to help the yacht and clean a snout.",
        f'Write a child-friendly fairy tale that includes the words "yacht" and "snout" and ends happily.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    fairy, yacht, snout, prize = f["fairy"], f["yacht"], f["snout"], f["prize"]
    return [
        QAItem(
            question=f"Who helped the yacht at the harbor?",
            answer=f"{fairy.id}, a little fairy who loved magic, helped the yacht with a kind spell.",
        ),
        QAItem(
            question=f"What was wrong with the snout near the yacht?",
            answer=f"The snout was muddy and messy, so the yacht's bow looked dull until the magic cleaned it.",
        ),
        QAItem(
            question=f"What did the magic do for the prize?",
            answer=f"It made the {prize.label} glow gold again and helped the yacht look bright for the festival sail.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a yacht?",
            answer="A yacht is a boat that sails on the water, often smooth and bright like a little ship.",
        ),
        QAItem(
            question="What is a snout?",
            answer="A snout is the nose or nose-like front part of some animals, and it can get muddy or clean.",
        ),
        QAItem(
            question="What is magic in a fairy tale?",
            answer="Magic is a special force in fairy tales that can change things in wonderful ways.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,S,T) :- place(P), spell(S), prize(T), harbor(P), magic_place(P), kind_spell(S), magical_prize(T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.harbor:
            lines.append(asp.fact("harbor", pid))
        if "magic" in p.affords:
            lines.append(asp.fact("magic_place", pid))
    for sid, s in SPELLS.items():
        lines.append(asp.fact("spell", sid))
        if s.requires_kindness:
            lines.append(asp.fact("kind_spell", sid))
    for tid, t in PRIZES.items():
        lines.append(asp.fact("prize", tid))
        if t.magical:
            lines.append(asp.fact("magical_prize", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="harbor", spell="moon_dust", prize="figurehead", fairy="Pippa", snout_owner="Seal"),
    StoryParams(place="bay", spell="kind_breeze", prize="snout", fairy="Luna", snout_owner="Sea Lion"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            s = generate(params)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
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
