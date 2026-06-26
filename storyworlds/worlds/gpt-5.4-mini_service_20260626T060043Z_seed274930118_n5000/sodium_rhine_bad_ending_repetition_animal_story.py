#!/usr/bin/env python3
"""
Storyworld: sodium_rhine_bad_ending_repetition_animal_story

A small animal-story simulation set by the Rhine, built around sodium, repeated
warnings, and a sad ending that follows from the hero's stubborn loop.

The premise is simple: a little animal finds something salty near the river and
keeps trying again and again to make it theirs. The repeated choice makes the
mess worse, and the ending proves the loss.

This file follows the Storyweavers world contract:
- one self-contained stdlib script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    setting_word: str
    affords: set[str] = field(default_factory=set)
    wet: bool = False


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    salty: bool = False
    safe: bool = False
    owners: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    repeat_line: str
    risk: str
    mess: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    items: dict[str, Item] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)
    zone: set[str] = field(default_factory=set)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
    place: str
    action: str
    item: str
    name: str
    gender: str
    companion: str
    trait: str
    seed: Optional[int] = None


PLACES = {
    "rhine_bank": Place(
        id="rhine_bank",
        label="the Rhine bank",
        setting_word="Rhine",
        affords={"taste", "carry"},
        wet=True,
    ),
    "river_path": Place(
        id="river_path",
        label="the path by the Rhine",
        setting_word="Rhine",
        affords={"taste", "carry"},
        wet=True,
    ),
}

ACTIONS = {
    "taste_salt": Action(
        id="taste_salt",
        verb="taste the sodium",
        gerund="tasting the sodium",
        repeat_line="again and again",
        risk="too salty",
        mess="salty",
        zone={"mouth", "hands"},
        keyword="sodium",
        tags={"sodium", "salt", "rhine"},
    ),
    "carry_salt": Action(
        id="carry_salt",
        verb="carry the sodium pouch",
        gerund="carrying the sodium pouch",
        repeat_line="again and again",
        risk="leaky",
        mess="spilled",
        zone={"hands"},
        keyword="sodium",
        tags={"sodium", "rhine"},
    ),
}

ITEMS = {
    "sodium": Item(
        id="sodium",
        label="sodium",
        phrase="a shiny little sodium crystal",
        type="sodium",
        region="hands",
        salty=True,
        safe=False,
        owners={"bird", "otter", "mouse"},
    ),
    "sodium_pouch": Item(
        id="sodium_pouch",
        label="sodium pouch",
        phrase="a tiny cloth pouch of sodium",
        type="pouch",
        region="hands",
        salty=True,
        safe=False,
        owners={"bird", "otter", "mouse"},
    ),
}

GIRL_NAMES = ["Luna", "Mina", "Nora", "Zoe", "Iris"]
BOY_NAMES = ["Finn", "Timo", "Bram", "Levi", "Otto"]
TRAITS = ["curious", "brave", "quiet", "playful", "small"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES.values():
        for action in ACTIONS.values():
            for item in ITEMS.values():
                if "Rhine" in place.setting_word and item.salty and "sodium" in action.tags:
                    out.append((place.id, action.id, item.id))
    return out


def explain_rejection(action: Action, item: Item) -> str:
    return (
        f"(No story: {action.verb} only makes sense with a salty sodium item, and "
        f"{item.label} does not fit that premise.)"
    )


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get(world.facts["hero"].id)
    action: Action = world.facts["action"]
    if hero.memes["try"] < THRESHOLD:
        return out
    sig = ("repeat", hero.id, action.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["loop"] += 1
    out.append("The same try came back again.")
    return out


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get(world.facts["hero"].id)
    item = world.items[world.facts["item"].id]
    action: Action = world.facts["action"]
    if hero.meters["salty"] < THRESHOLD:
        return out
    sig = ("soak", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.safe = False
    hero.memes["regret"] += 1
    out.append(f"{hero.id}'s paws got salty, and the {item.label} felt worse.")
    return out


CAUSAL_RULES = [Rule("repeat", _r_repeat), Rule("soak", _r_soak)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(place: Place, action: Action, item_cfg: Item, hero_name: str, hero_gender: str,
         companion_type: str, trait: str) -> World:
    world = World(place=place)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_gender, traits=["little", trait, "stubborn"]
    ))
    companion = world.add(Entity(
        id="Companion", kind="character", type=companion_type, label=f"the {companion_type}"
    ))
    item = Item(**{k: getattr(item_cfg, k) for k in item_cfg.__dataclass_fields__})
    world.items[item.id] = item

    world.say(f"{hero.id} was a little {trait} {hero.type} who lived near {place.label}.")
    world.say(f"{hero.id} loved {action.gerund}, and {companion.label} always watched the river.")
    world.say(f"One day, {hero.id} found {item.phrase} on the bank of the Rhine.")
    world.say(f"{hero.id} loved it and kept it close.")

    world.para()
    world.say(f"By the water, {hero.id} wanted to {action.verb} {action.repeat_line}.")
    hero.memes["try"] += 1
    hero.meters["salty"] += 1
    world.zone = set(action.zone)
    world.say(f"{companion.label.capitalize()} warned, 'That will leave {hero.pronoun('object')} {action.risk}.'")
    world.say(f"But {hero.id} tried {action.repeat_line} anyway.")
    propagate(world, narrate=True)

    world.para()
    item.safe = False
    hero.memes["sad"] += 1
    world.say(
        f"At last, the Rhine water took the {item.label} away, and {hero.id} had to stand with empty paws."
    )
    world.say(
        f"{hero.id} looked at the ripples, said '{action.repeat_line}', and no one could bring the little treasure back."
    )

    world.facts.update(hero=hero, companion=companion, item=item, action=action, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    action = f["action"]
    item = f["item"]
    return [
        f'Write a short animal story about {hero.id} by the Rhine, using the word "sodium".',
        f"Tell a gentle but sad story where an animal keeps trying {action.repeat_line} and loses {item.label}.",
        f'Write an animal story set near the Rhine with repetition and a bad ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    comp: Entity = f["companion"]
    item: Item = f["item"]
    action: Action = f["action"]
    return [
        QAItem(
            question=f"Who is the story about near the Rhine?",
            answer=f"It is about {hero.id}, a little {hero.type} who lives by the Rhine.",
        ),
        QAItem(
            question=f"What did {hero.id} keep trying to do {action.repeat_line}?",
            answer=f"{hero.id} kept trying to {action.verb} {action.repeat_line}.",
        ),
        QAItem(
            question=f"What did {hero.id} find on the bank?",
            answer=f"{hero.id} found {item.phrase} on the bank of the Rhine.",
        ),
        QAItem(
            question=f"Why was the ending sad?",
            answer=f"The ending was sad because the Rhine water took the {item.label} away and {hero.id} could not get it back.",
        ),
        QAItem(
            question=f"Who warned {hero.id}?",
            answer=f"{comp.label.capitalize()} warned {hero.id} that the sodium would leave {hero.pronoun('object')} {action.risk}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sodium?",
            answer="Sodium is a soft, silvery chemical element. In stories for kids, it can stand for a salty crystal or salty mineral.",
        ),
        QAItem(
            question="What is the Rhine?",
            answer="The Rhine is a big river in Europe. Rivers carry water past banks, boats, and animals living nearby.",
        ),
        QAItem(
            question="What does repetition mean in a story?",
            answer="Repetition means a part of the story happens more than once, like a character saying or trying the same thing again and again.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    for iid, item in world.items.items():
        lines.append(f"  {iid:8} (item   ) safe={item.safe} salty={item.salty}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="rhine_bank", action="taste_salt", item="sodium", name="Nori", gender="otter", companion="heron", trait="curious"),
    StoryParams(place="river_path", action="carry_salt", item="sodium_pouch", name="Tilo", gender="mouse", companion="duck", trait="playful"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world by the Rhine with sodium, repetition, and a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["otter", "mouse", "duck", "bird"])
    ap.add_argument("--companion", choices=["heron", "duck", "bird", "mouse"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.action and args.item:
        if not (args.item == "sodium" or args.item == "sodium_pouch"):
            raise StoryError(explain_rejection(ACTIONS[args.action], ITEMS[args.item]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, item = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["otter", "mouse", "duck", "bird"])
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    companion = args.companion or rng.choice(["heron", "duck", "bird", "mouse"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, action=action, item=item, name=name, gender=gender, companion=companion, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        ACTIONS[params.action],
        ITEMS[params.item],
        params.name,
        params.gender,
        params.companion,
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


ASP_RULES = r"""
valid(P,A,I) :- place(P), action(A), item(I),
                sodium_item(I), rhine_place(P), sodium_action(A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        if "Rhine" in PLACES[pid].setting_word:
            lines.append(asp.fact("rhine_place", pid))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
        if "sodium" in ACTIONS[aid].tags:
            lines.append(asp.fact("sodium_action", aid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.salty:
            lines.append(asp.fact("sodium_item", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    c, p = set(asp_valid_combos()), set(valid_combos())
    if c == p:
        print(f"OK: clingo gate matches valid_combos() ({len(c)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if c - p:
        print("  only in clingo:", sorted(c - p))
    if p - c:
        print("  only in python:", sorted(p - c))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

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
            header = f"### {p.name}: {p.action} at {p.place} (item: {p.item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
