#!/usr/bin/env python3
"""
storyworlds/worlds/provide_alien_conjunction_humor_suspense_fairy_tale.py
=========================================================================

A small fairy-tale storyworld about a tiny alien visitor, a tricky missing
conjunction, and a humorous suspenseful promise to provide the right thing at
the right time.

Seeded premise:
---
In a moonlit fairy tale valley, a little alien lands beside a speaking bridge
and asks to provide a conjunction so two stuck paths can join. The bridge
keeper worries the alien will muddle the royal lantern and make the crossing
go wrong. After a tense pause and a funny mix-up about grammar versus glue,
the alien provides the conjunction, the paths join safely, and everyone laughs
beneath the stars.

The world model tracks:
- physical meters: sparkle, wobble, shine, soot
- emotional memes: worry, courage, humor, relief, curiosity

The story is intentionally narrow: a few plausible variants, all with an honest
problem, a causal turn, and a resolution image that proves what changed.
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

SETTING_WORD = "fairy tale valley"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "witch"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "wizard"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool = False
    hazard: str = "wobble"
    affords: set[str] = field(default_factory=set)


@dataclass
class Need:
    id: str
    verb: str
    gerund: str
    risk: str
    zone: str
    hazard: str
    keyword: str = "conjunction"


@dataclass
class Aid:
    id: str
    label: str
    fix: str
    prep: str
    tail: str


@dataclass
class StoryParams:
    place: str
    need: str
    aid: str
    hero_name: str
    hero_type: str
    keeper_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.last_joke: str = ""

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.last_joke = self.last_joke
        return c


THRESHOLD = 1.0


PLACES = {
    "bridge": Place("the moon bridge", indoors=False, hazard="wobble", affords={"cross"}),
    "garden": Place("the singing garden", indoors=False, hazard="mist", affords={"gather"}),
    "tower": Place("the lantern tower", indoors=True, hazard="soot", affords={"lift"}),
}

NEEDS = {
    "cross": Need(
        id="cross",
        verb="cross the bridge",
        gerund="crossing the bridge",
        risk="wobbly",
        zone="bridge",
        hazard="wobble",
        keyword="conjunction",
    ),
    "gather": Need(
        id="gather",
        verb="gather the moonflowers",
        gerund="gathering moonflowers",
        risk="misty",
        zone="garden",
        hazard="mist",
        keyword="and",
    ),
    "lift": Need(
        id="lift",
        verb="lift the lantern",
        gerund="lifting the lantern",
        risk="sooty",
        zone="tower",
        hazard="soot",
        keyword="but",
    ),
}

AIDS = {
    "glue": Aid("glue", "a little golden glue", "bind the broken bridge planks", "bring a pot of golden glue", "brought the golden glue and fixed the join"),
    "ribbon": Aid("ribbon", "a bright ribbon", "tie the two signs together", "carry a bright ribbon", "carried the ribbon and tied the signs"),
    "lampcloth": Aid("lampcloth", "a clean lampcloth", "wipe the lantern clear", "fetch a clean lampcloth", "fetched the lampcloth and shined the lantern"),
}

TRAITS = ["curious", "cheerful", "brave", "mischievous", "polite"]
HERO_TYPES = ["alien", "sprite", "child"]
KEEPER_TYPES = ["keeper", "queen", "bridge-keeper"]


def is_reasonable(place: Place, need: Need, aid: Aid) -> bool:
    return need.id in place.affords and aid.id in {"glue", "ribbon", "lampcloth"}


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pk, place in PLACES.items():
        for nk, need in NEEDS.items():
            for ak, aid in AIDS.items():
                if is_reasonable(place, need, aid):
                    out.append((pk, nk, ak))
    return out


def predict(world: World, hero: Entity, need: Need) -> bool:
    sim = world.copy()
    hero2 = sim.get(hero.id)
    hero2.memes["worry"] += 1
    hero2.meters[need.hazard] = hero2.meters.get(need.hazard, 0) + 1
    return hero2.meters[need.hazard] >= THRESHOLD


def intro(world: World, hero: Entity, keeper: Entity) -> None:
    world.say(
        f"Once in {SETTING_WORD}, there lived a {hero.memes.get('trait_word', 'little')} "
        f"{hero.type} named {hero.id} who had shiny antennae and a very serious smile."
    )
    world.say(
        f"At the edge of the path stood {keeper.label}, who liked rules almost as much as tea."
    )


def setup(world: World, hero: Entity, need: Need) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"{hero.id} loved {need.gerund}, because every step felt like a small adventure."
    )


def warning(world: World, keeper: Entity, hero: Entity, need: Need) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"But the {world.place.hazard} around {world.place.name} made the path look {need.risk}."
    )
    world.say(
        f'"You must not {need.verb} without help," {keeper.label} said. '
        f'"The bridge is grumpy tonight."'
    )


def joke_turn(world: World, hero: Entity, keeper: Entity) -> None:
    hero.memes["humor"] = hero.memes.get("humor", 0) + 1
    world.last_joke = "The alien asked whether a conjunction came with a cape and a cape-stand."
    world.say(
        f"{hero.id} blinked and said, \"I can provide a conjunction!\" Then {hero.pronoun()} "
        f"held up two tiny fingers and added, \"I brought the word and the glue.\""
    )
    world.say(
        f"{keeper.label} stared, then snorted. \"I meant a joining thing, not a grammar lesson,\" "
        f"{keeper.pronoun('subject')} said."
    )


def fix(world: World, hero: Entity, keeper: Entity, need: Need, aid: Aid) -> None:
    hero.memes["courage"] = hero.memes.get("courage", 0) + 1
    hero.meters[need.hazard] = hero.meters.get(need.hazard, 0) + 1
    world.say(
        f"Still, {hero.id} {aid.prep}, because the bridge needed a careful join."
    )
    if aid.id == "glue":
        world.say(
            f"{hero.id} brushed the gold glue across the cracked plank, and the bridge stopped wobbling."
        )
    elif aid.id == "ribbon":
        world.say(
            f"{hero.id} tied the signs together, and the windy arrows stopped arguing."
        )
    else:
        world.say(
            f"{hero.id} wiped the lantern until it glowed like a smiling moon."
        )


def resolution(world: World, hero: Entity, keeper: Entity, need: Need, aid: Aid) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    hero.memes["worry"] = 0
    world.say(
        f"At last, the path became safe, and {hero.id} could {need.verb} without a single shake."
    )
    world.say(
        f"{keeper.label} laughed so hard that {keeper.pronoun('possessive')} teacup jingled."
    )
    world.say(
        f"In the end, {hero.id} had truly provided a conjunction: not only a word, but a clever joining."
    )


def tell(place: Place, need: Need, aid: Aid, hero_name: str, hero_type: str, keeper_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    keeper = world.add(Entity(id="keeper", kind="character", type=keeper_type, label="the bridge keeper"))
    hero.memes["trait_word"] = trait

    intro(world, hero, keeper)
    world.para()
    setup(world, hero, need)
    warning(world, keeper, hero, need)
    joke_turn(world, hero, keeper)
    world.para()
    fix(world, hero, keeper, need, aid)
    resolution(world, hero, keeper, need, aid)

    world.facts.update(hero=hero, keeper=keeper, need=need, aid=aid, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, need, aid = f["hero"], f["need"], f["aid"]
    return [
        f'Write a short fairy tale for a child about an {hero.type} who must provide a conjunction to {need.verb}.',
        f"Tell a humorous, suspenseful story where {hero.id} thinks a conjunction is both a word and a tool.",
        f"Write a gentle fairy tale in which {hero.id} uses {aid.label} to solve a tricky {need.keyword} problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, keeper, need, aid, place = f["hero"], f["keeper"], f["need"], f["aid"], f["place"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little {hero.type} who came to {place.name}.",
        ),
        QAItem(
            question=f"Why did {keeper.label} warn {hero.id} not to {need.verb} right away?",
            answer=(
                f"{keeper.label} warned {hero.id} because {place.name} was {place.hazard} and "
                f"{need.gerund} could go wrong there."
            ),
        ),
        QAItem(
            question=f"What was funny about {hero.id}'s idea to provide a conjunction?",
            answer=(
                f"{hero.id} first acted like a conjunction was a grammar word, then used it like a clever joining thing. "
                f"That mix-up made the keeper laugh."
            ),
        ),
        QAItem(
            question=f"How was the problem solved in the end?",
            answer=(
                f"{hero.id} used {aid.label} to make the join safe, so the path stopped wobbling and "
                f"{hero.id} could {need.verb}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a conjunction?",
            answer="A conjunction is a word that joins parts of a sentence, like and, but, or so.",
        ),
        QAItem(
            question="What does an alien mean?",
            answer="An alien is a being from another world or a faraway place beyond Earth.",
        ),
        QAItem(
            question="Why can a bridge be tricky at night?",
            answer="A bridge can be tricky at night because it can be hard to see and may feel wobbly or scary.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:10}) meters={meters} memes={memes}")
    lines.append(f"  last joke: {world.last_joke}")
    return "\n".join(lines)


CURATED = [
    StoryParams("bridge", "cross", "glue", "Milo", "alien", "keeper", "curious"),
    StoryParams("garden", "gather", "ribbon", "Pip", "alien", "queen", "cheerful"),
    StoryParams("tower", "lift", "lampcloth", "Tavi", "alien", "keeper", "mischievous"),
]


ASP_RULES = r"""
place(P) :- setting(P).
need(N) :- need_id(N).
aid(A) :- aid_id(A).

reasonable(P,N,A) :- affords(P,N), aid_ok(A), need_ok(N).
valid_story(P,N,A) :- reasonable(P,N,A).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("setting", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
        for n in sorted(place.affords):
            lines.append(asp.fact("affords", pid, n))
    for nid in NEEDS:
        lines.append(asp.fact("need_id", nid))
    for aid in AIDS:
        lines.append(asp.fact("aid_id", aid))
        lines.append(asp.fact("aid_ok", aid))
    for nid in NEEDS:
        lines.append(asp.fact("need_ok", nid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about an alien, a conjunction, and a funny rescue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["alien", "sprite", "child"])
    ap.add_argument("--keeper-type", choices=["keeper", "queen", "bridge-keeper"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.need is None or c[1] == args.need)
              and (args.aid is None or c[2] == args.aid)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, need, aid = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        need=need,
        aid=aid,
        hero_name=args.name or rng.choice(["Milo", "Pip", "Tavi", "Nova"]),
        hero_type=args.hero_type or "alien",
        keeper_type=args.keeper_type or rng.choice(["keeper", "queen", "bridge-keeper"]),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        NEEDS[params.need],
        AIDS[params.aid],
        params.hero_name,
        params.hero_type,
        params.keeper_type,
        params.trait,
    )
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
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for place, need, aid in triples:
            print(f"  {place:8} {need:8} {aid:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
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
            header = f"### {p.hero_name}: {p.need} at {p.place} ({p.aid})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
