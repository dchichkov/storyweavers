#!/usr/bin/env python3
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Venue:
    place: str = "the lawn"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    safety: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Disguise:
    id: str
    label: str
    phrase: str
    reveals: str
    helps: str
    plan: str
    reject_reason: str


class World:
    def __init__(self, venue: Venue) -> None:
        self.venue = venue
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
class StoryParams:
    venue: str
    item: str
    disguise: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


VENUES = {
    "lawn": Venue(place="the lawn", indoor=False, affords={"croquet"}),
    "park": Venue(place="the park", indoor=False, affords={"croquet"}),
    "garden": Venue(place="the garden", indoor=False, affords={"croquet"}),
}

ITEMS = {
    "mallet": Item(
        id="mallet",
        label="croquet mallet",
        phrase="a smooth croquet mallet",
        type="mallet",
        safety="heavy",
    ),
    "ball": Item(
        id="ball",
        label="croquet ball",
        phrase="a bright croquet ball",
        type="ball",
        safety="rolls away",
    ),
    "bow": Item(
        id="bow",
        label="croquet bow tie",
        phrase="a tiny bow tie for the game",
        type="bow",
        safety="snags easily",
    ),
}

DISGUISES = {
    "mask": Disguise(
        id="mask",
        label="mask",
        phrase="a funny paper mask",
        reveals="barely see where the ball was going",
        helps="practice pretend play at home",
        plan="put the mask away before the game",
        reject_reason="a mask makes it hard to watch the ball and could keep a child from playing safely",
    ),
    "cape": Disguise(
        id="cape",
        label="cape",
        phrase="a bright cape",
        reveals="trip on the cape hem",
        helps="play dress-up in the bedroom",
        plan="hang the cape on a hook until after croquet",
        reject_reason="a cape can drag on the grass and get in the way of a careful swing",
    ),
    "mustache": Disguise(
        id="mustache",
        label="fake mustache",
        phrase="a silly fake mustache",
        reveals="feel silly and hard to speak clearly",
        helps="be a pretend detective at home",
        plan="save the mustache for later",
        reject_reason="a fake mustache is funny, but it can make talking to friends awkward during the game",
    ),
}

NAMES_GIRL = ["Mia", "Lena", "Ava", "Zoe", "Nora", "Iris"]
NAMES_BOY = ["Leo", "Max", "Ben", "Noah", "Theo", "Finn"]
TRAITS = ["careful", "curious", "bright", "quiet", "playful", "thoughtful"]


def valid_combo(venue: Venue, item: Item, disguise: Disguise) -> bool:
    return "croquet" in venue.affords and item.type in {"mallet", "ball", "bow"} and disguise.id in DISGUISES


def valid_combos() -> list[tuple[str, str, str]]:
    return [(v, i, d) for v in VENUES for i in ITEMS for d in DISGUISES]


def explain_rejection(item: Item, disguise: Disguise) -> str:
    return f"(No story: {disguise.reject_reason} The cautionary slice-of-life version needs a disguise that can be set aside for croquet.)"


def tell(venue: Venue, item: Item, disguise: Disguise, hero_name: str, hero_type: str, hero_traits: list[str], parent_type: str) -> World:
    world = World(venue)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={"joy": 0.0}, memes={"want": 0.0, "worry": 0.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}", meters={"care": 0.0}, memes={"caution": 0.0}))
    prize = world.add(Entity(id=item.id, type=item.type, label=item.label, phrase=item.phrase, owner=hero.id))
    world.facts.update(hero=hero, parent=parent, prize=prize, disguise=disguise, venue=venue)

    world.say(f"{hero.id} was a {hero_traits[0]} little {hero.type} who liked quiet afternoons on {venue.place}.")
    world.say(f"{hero.pronoun().capitalize()} also loved {disguise.phrase}, because it made ordinary days feel like a game.")
    world.say(f"One morning, {hero.id}'s {parent_type} brought out {prize.phrase} and said it was time for croquet.")

    world.para()
    hero.memes["want"] += 1
    world.say(f"{hero.id} wanted to wear {disguise.label} to the lawn, but {hero.pronoun('possessive')} {parent_type} noticed the problem right away.")
    world.say(f"\"That could {disguise.reveals},\" {parent.pronoun().capitalize()} said. \"And croquet asks for careful eyes and easy steps.\"")
    hero.memes["worry"] += 1
    parent.memes["caution"] += 1

    world.para()
    world.say(f"{hero.id} looked at {prize.label}, then at {disguise.label}, and thought about the game.")
    world.say(f"At last, {hero.id} nodded and chose to {disguise.plan}.")
    world.say(f"That way, {hero.id} could play croquet, keep {prize.label} safe, and still have dress-up fun later at home.")
    hero.meters["joy"] += 1
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short slice-of-life story for a small child that includes "{f["venue"].place}" and croquet.',
        f"Tell a cautionary story where {f['hero'].id} wants to wear a disguise but learns to set it aside for a careful game.",
        f"Write a gentle story about a child, a disguise, and croquet, ending with a safe choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, disguise = f["hero"], f["parent"], f["prize"], f["disguise"]
    return [
        QAItem(
            question=f"What did {hero.id} want to wear when croquet was about to start?",
            answer=f"{hero.id} wanted to wear {disguise.label}, but {hero.pronoun('possessive')} {parent.type} said it would get in the way.",
        ),
        QAItem(
            question=f"Why did {parent.id} warn {hero.id} about the disguise?",
            answer=f"{parent.id} warned {hero.id} because {disguise.reveals}, and croquet needs careful watching and easy steps.",
        ),
        QAItem(
            question=f"What choice did {hero.id} make in the end?",
            answer=f"{hero.id} decided to {disguise.plan}, so the child could play croquet safely and save the disguise for later.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is croquet?", answer="Croquet is a lawn game where players use mallets to hit balls through hoops."),
        QAItem(question="What is a disguise?", answer="A disguise is something a person wears to look different or pretend to be someone else."),
        QAItem(question="Why should a child be careful with a heavy game tool?", answer="A heavy game tool can be hard to control, so careful hands help keep people and things safe."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
croquet_game(V,I,D) :- venue(V), item(I), disguise(D), affords(V,croquet).
reasonable(V,I,D) :- croquet_game(V,I,D), safe_item(I), cautionary_disguise(D).
#show reasonable/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for vid, v in VENUES.items():
        lines.append(asp.fact("venue", vid))
        for a in sorted(v.affords):
            lines.append(asp.fact("affords", vid, a))
    for iid, it in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if it.type in {"ball", "mallet", "bow"}:
            lines.append(asp.fact("safe_item", iid))
    for did, d in DISGUISES.items():
        lines.append(asp.fact("disguise", did))
        lines.append(asp.fact("cautionary_disguise", did))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_reasonable_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in clingo:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary slice-of-life croquet story world with disguises.")
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--disguise", choices=DISGUISES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    combos = valid_combos()
    if args.venue:
        combos = [c for c in combos if c[0] == args.venue]
    if args.item:
        combos = [c for c in combos if c[1] == args.item]
    if args.disguise:
        combos = [c for c in combos if c[2] == args.disguise]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    venue, item, disguise = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(venue=venue, item=item, disguise=disguise, name=hero_name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(VENUES[params.venue], ITEMS[params.item], DISGUISES[params.disguise], params.name, params.gender, [params.trait], params.parent)
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
    StoryParams(venue="lawn", item="mallet", disguise="mask", name="Mia", gender="girl", parent="mother", trait="careful"),
    StoryParams(venue="garden", item="ball", disguise="cape", name="Leo", gender="boy", parent="father", trait="curious"),
    StoryParams(venue="park", item="bow", disguise="mustache", name="Ava", gender="girl", parent="mother", trait="playful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_reasonable_combos()
        print(f"{len(combos)} compatible combinations:\n")
        for c in combos:
            print("  ", c)
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
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.name}: {p.disguise} + {p.item} at {p.venue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
