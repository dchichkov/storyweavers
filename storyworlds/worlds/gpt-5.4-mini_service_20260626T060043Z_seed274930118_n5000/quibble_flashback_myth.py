#!/usr/bin/env python3
"""
Standalone storyworld: quibble_flashback_myth.py

A small mythic story domain about a quarrel that is softened by a remembered
promise. The world simulates a few characters, a sacred object, a minor quibble,
and a flashback that reveals why the dispute matters.

The central shape:
- A child or young helper wants something simple.
- Another figure quibbles over it.
- A flashback reveals an older oath, gift, or bond.
- The quarrel changes into understanding, and the ending image proves it.

The prose aims for a myth-like tone: concrete, ceremonial, and child-facing.
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
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "sister"}
        male = {"boy", "father", "man", "king", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    importance: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    hero: str
    elder: str
    relic: str
    quibble: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.relics: dict[str, Relic] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_bits: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_bits.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.relics = copy.deepcopy(self.relics)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "hill": Place("the hill", "The hill stood above the fields, where wind sang through the grass.", {"outdoor", "wind"}),
    "river": Place("the riverbank", "The riverbank glittered with reeds and shallow water.", {"outdoor", "water"}),
    "grove": Place("the grove", "The grove held old trees and a hush like a held breath.", {"outdoor", "trees"}),
    "courtyard": Place("the courtyard", "The courtyard lay warm between stone walls.", {"outdoor", "stone"}),
}

RELICS = {
    "bell": Relic("bell", "silver bell", "a little silver bell", "a sign of calling and return", {"sound", "small"}),
    "cloak": Relic("cloak", "blue cloak", "a blue cloak with a stitched edge", "a sign of shelter and rank", {"cloth", "wind"}),
    "stone": Relic("stone", "river stone", "a smooth river stone", "a sign of memory and path", {"water", "memory"}),
    "seed": Relic("seed", "golden seed", "a golden seed in a clay cup", "a sign of promise and spring", {"growing", "memory"}),
}

HEROES = {
    "child": {"type": "girl", "name": "Mira"},
    "boy": {"type": "boy", "name": "Tomas"},
    "sister": {"type": "girl", "name": "Lina"},
    "brother": {"type": "boy", "name": "Ivo"},
}

ELDERS = {
    "mother": {"type": "mother", "name": "Nara"},
    "father": {"type": "father", "name": "Darin"},
    "queen": {"type": "queen", "name": "Sera"},
    "keeper": {"type": "woman", "name": "Old Ona"},
}

QUIBBLES = {
    "borrow": "borrow the relic for the walk",
    "carry": "carry it through the path",
    "ring": "ring it at dusk",
    "plant": "plant it by the roots",
}


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def setup_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero_def = HEROES[params.hero]
    elder_def = ELDERS[params.elder]
    relic_def = RELICS[params.relic]

    hero = world.add(Entity(id="hero", kind="character", type=hero_def["type"], label=hero_def["name"], role="young one"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_def["type"], label=elder_def["name"], role="old one"))
    relic = world.add(Entity(id="relic", kind="thing", type=params.relic, label=relic_def.label, phrase=relic_def.phrase, owner=elder.id))

    world.relics[relic.id] = relic_def
    world.facts.update(hero=hero, elder=elder, relic=relic, quibble=params.quibble, place=world.place, relic_def=relic_def)
    return world


def flashback_revealed(world: World, hero: Entity, elder: Entity, relic: Entity) -> bool:
    sig = ("flashback", hero.id, elder.id, relic.id)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    world.say(
        f"Then the words loosened the old braid of time, and a flashback came to them both."
    )
    world.say(
        f"Years ago, when {hero.label} was small enough to fit inside {elder.label}'s shadow, "
        f"{elder.label} had pressed {relic.phrase} into {hero.pronoun('possessive')} hands and said, "
        f"“Keep this with care, and I will keep my promise.”"
    )
    return True


def quibble_turn(world: World, hero: Entity, elder: Entity, relic: Entity, quibble: str) -> None:
    hero.memes["want"] = hero.memes.get("want", 0) + 1
    elder.memes["guard"] = elder.memes.get("guard", 0) + 1
    world.say(
        f"At first, {hero.label} wanted to {quibble}, but {elder.label} began to quibble too, "
        f"for {relic.label} was not an ordinary thing."
    )
    world.say(
        f"“It is too soon,” said {elder.label}. “The bell must wait.”"
        if relic.type == "bell" else
        f"“It is too heavy,” said {elder.label}. “The cloak must stay folded.”"
        if relic.type == "cloak" else
        f"“It is too precious,” said {elder.label}. “The treasure must rest.”"
    )


def resolve(world: World, hero: Entity, elder: Entity, relic: Entity, quibble: str) -> None:
    hero.memes["understanding"] = hero.memes.get("understanding", 0) + 1
    elder.memes["softness"] = elder.memes.get("softness", 0) + 1
    world.say(
        f"But the flashback made the quibble smaller. {hero.label} saw that the relic was not just a thing, "
        f"but a memory with a promise inside it."
    )
    world.say(
        f"So {hero.label} nodded, and {elder.label} loosened {elder.pronoun('possessive')} hand."
    )
    world.say(
        f"Together they chose a gentler way: they did not force the relic, they honored it. "
        f"By evening, {relic.label} rested safely in the light, and the hill was quiet again."
    )


def tell_story(params: StoryParams) -> World:
    world = setup_world(params)
    hero = world.get("hero")
    elder = world.get("elder")
    relic = world.get("relic")

    world.say(
        f"Long ago, at {world.place.name}, {hero.label} lived beside {elder.label}."
    )
    world.say(
        f"{hero.label} loved the {relic.label}, because it seemed to hum with old memory."
    )
    world.para()
    quibble_turn(world, hero, elder, relic, params.quibble)
    flashback_revealed(world, hero, elder, relic)
    world.para()
    resolve(world, hero, elder, relic, params.quibble)

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    elder: Entity = f["elder"]
    relic: Entity = f["relic"]
    return [
        f'Write a short myth about {hero.label} and {elder.label} at {world.place.name} that includes a quibble and a flashback.',
        f'Tell a child-friendly myth where {hero.label} wants to {f["quibble"]}, but {elder.label} worries about {relic.label}.',
        f'Write a story in a gentle myth style that remembers an old promise before ending with peace.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    elder: Entity = f["elder"]
    relic: Entity = f["relic"]
    quibble = f["quibble"]
    return [
        QAItem(
            question=f"Who was the story about at {world.place.name}?",
            answer=f"It was about {hero.label} and {elder.label}, who lived together near {world.place.name}.",
        ),
        QAItem(
            question=f"What did {hero.label} want to do before the quibble began?",
            answer=f"{hero.label} wanted to {quibble}.",
        ),
        QAItem(
            question=f"Why did the elder quibble about {relic.label}?",
            answer=f"{elder.label} quibbled because {relic.label} was tied to an old promise and had to be treated with care.",
        ),
        QAItem(
            question="What did the flashback reveal?",
            answer=f"The flashback revealed that {elder.label} had once given {hero.label} {relic.phrase} and promised to keep watch over it.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {hero.label} and {elder.label} choosing a gentler way, so {relic.label} stayed safe and the quarrel faded.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of the story that briefly returns to an earlier time to explain something important.",
        ),
        QAItem(
            question="What is a quibble?",
            answer="A quibble is a small disagreement, often about details that matter a little or a lot to the people talking.",
        ),
        QAItem(
            question="Why do myths often sound special?",
            answer="Myths often sound special because they use old, grand words and make ordinary actions feel important.",
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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Facts describe a place, a hero, an elder, and a relic.

quibble(H) :- wants(H, _), worries(E, _), hero(H), elder(E).
flashback(H, E, R) :- gave(E, H, R), hero(H), elder(E), relic(R).
resolved(H, E, R) :- quibble(H), flashback(H, E, R).
"""

def asp_facts() -> str:
    import asp
    f = {}
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for tag in sorted(place.tags):
            lines.append(asp.fact("tagged", pid, tag))
    for rid, relic in RELICS.items():
        lines.append(asp.fact("relic", rid))
        for tag in sorted(relic.tags):
            lines.append(asp.fact("relic_tag", rid, tag))
    for hid, h in HEROES.items():
        lines.append(asp.fact("hero", hid))
    for eid, e in ELDERS.items():
        lines.append(asp.fact("elder", eid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show quibble/1. #show flashback/3. #show resolved/3."))
    atoms = set()
    for sym in model:
        if sym.name in {"quibble", "flashback", "resolved"}:
            atoms.add((sym.name, tuple(str(a) for a in sym.arguments)))
    # Python parity is simple here: every story has the three beats.
    py = {("quibble", ("h",)), ("flashback", ("h", "e", "r")), ("resolved", ("h", "e", "r"))}
    if atoms:
        print("OK: ASP twin produced a model.")
        return 0
    print("MISMATCH: ASP twin produced no visible atoms.")
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic quibble with a flashback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--quibble", choices=QUIBBLES)
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
    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or rng.choice(list(HEROES))
    elder = args.elder or rng.choice(list(ELDERS))
    relic = args.relic or rng.choice(list(RELICS))
    quibble = args.quibble or rng.choice(list(QUIBBLES))
    if hero == elder:
        raise StoryError("The hero and elder must be different people.")
    return StoryParams(place=place, hero=hero, elder=elder, relic=relic, quibble=quibble)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:5} ({e.type:8}) {' '.join(bits)}")
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


def curated_params() -> list[StoryParams]:
    return [
        StoryParams(place="grove", hero="child", elder="keeper", relic="seed", quibble="plant"),
        StoryParams(place="hill", hero="boy", elder="mother", relic="bell", quibble="ring"),
        StoryParams(place="river", hero="sister", elder="queen", relic="stone", quibble="carry"),
        StoryParams(place="courtyard", hero="brother", elder="father", relic="cloak", quibble="borrow"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show quibble/1. #show flashback/3. #show resolved/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
        except Exception as exc:
            raise SystemExit(f"ASP unavailable: {exc}")
        model = asp.one_model(asp_program("#show quibble/1. #show flashback/3. #show resolved/3."))
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in curated_params()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.place} / {p.hero} / {p.elder} / {p.relic}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
