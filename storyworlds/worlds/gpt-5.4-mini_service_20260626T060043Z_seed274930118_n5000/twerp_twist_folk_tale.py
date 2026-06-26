#!/usr/bin/env python3
"""
Storyworld: a folk tale with a twerp and a twist.

A small, classical simulation in a folk-tale style:
- a village child meets a greedy twerp
- the twerp causes trouble with a stolen thing
- a twist reveals the twerp's trick
- the community turns the trouble into a lesson and a tidy ending

This file is self-contained aside from the shared result/ASP helpers.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    taken: bool = False
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "grandmother", "aunt"}
        male = {"boy", "father", "man", "king", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    name: str
    kind: str
    old_magic: bool = False


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
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: callable


def _r_taken(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.kind != "thing" or not e.taken:
            continue
        if e.meters.get("missing", 0) >= THRESHOLD:
            continue
        sig = ("taken", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["missing"] = 1
        out.append(f"{e.label.capitalize()} had gone missing.")
    return out


def _r_twist(world: World) -> list[str]:
    out: list[str] = []
    twerp = next((e for e in world.entities.values() if e.type == "twerp"), None)
    trick = next((e for e in world.entities.values() if e.kind == "thing" and e.taken), None)
    if not twerp or not trick:
        return out
    if twerp.memes.get("caught", 0) >= THRESHOLD:
        return out
    if twerp.memes.get("showed_twist", 0) >= THRESHOLD:
        return out
    if trick.meters.get("missing", 0) < THRESHOLD:
        return out
    sig = ("twist", twerp.id, trick.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    twerp.memes["showed_twist"] = 1
    out.append("__twist__")
    return out


CAUSAL_RULES = [Rule("taken", _r_taken), Rule("twist", _r_twist)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__twist__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    twerp_name: str
    treasure: str
    seed: Optional[int] = None


PLACES = {
    "village": Place("the village green", "village"),
    "cottage": Place("the cottage lane", "lane"),
    "wood": Place("the old wood", "forest", old_magic=True),
    "market": Place("the market square", "market"),
}

TREASURES = {
    "bread": ("bread", "a round loaf of bread"),
    "bell": ("bell", "a little brass bell"),
    "cloak": ("cloak", "a red cloak"),
    "ring": ("ring", "a silver ring"),
}

HERO_NAMES = ["Mina", "Pip", "Lena", "Tob", "Nell", "Tom", "Ivy", "Finn"]
TWERP_NAMES = ["Snip", "Murk", "Wren", "Joss", "Brag", "Mottle", "Puck"]
TRAITS = ["kind", "curious", "brave", "cheerful", "careful"]


def tell(place: Place, hero_name: str, hero_type: str, twerp_name: str, treasure_key: str) -> World:
    world = World(place)
    treasure_label, treasure_phrase = TREASURES[treasure_key]

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name, memes={"hope": 1}))
    twerp = world.add(Entity(id=twerp_name, kind="character", type="twerp", label=twerp_name, memes={"greed": 1}))
    treasure = world.add(Entity(
        id="treasure",
        kind="thing",
        type=treasure_key,
        label=treasure_label,
        phrase=treasure_phrase,
        owner=hero.id,
    ))

    world.say(
        f"Long ago, in {place.name}, there lived a {random.choice(TRAITS)} child named {hero.id}. "
        f"{hero.pronoun('subject').capitalize()} treasured {treasure.phrase}."
    )
    world.say(
        f"Not far off lived {twerp.id}, a little twerp with a sly grin and busy fingers."
    )

    world.para()
    world.say(
        f"One bright day, {hero.id} set {treasure.pronoun('possessive') if False else 'the'} {treasure.label} near a stone wall to watch the birds."
    )
    treasure.taken = True
    treasure.carried_by = twerp.id
    twerp.memes["trick"] = 1
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{hero.id} looked up and cried, '{treasure.label.capitalize()}! Where did it go?' "
        f"{hero.pronoun('subject').capitalize()} searched under benches and behind hay carts."
    )
    world.say(
        f"Then the wind turned, and a twist came to the tale."
    )
    twerp.memes["caught"] = 1
    world.say(
        f"{twerp.id} slipped on a root, and the hidden {treasure.label} rolled right into the open."
    )
    treasure.carried_by = None
    treasure.taken = False

    world.para()
    world.say(
        f"{twerp.id} hung his head. 'I meant to boast, not to keep it,' {twerp.id} muttered. "
        f"{hero.id} took {treasure.phrase} back and did not strike him, for {hero.pronoun('subject')} had a steadier heart."
    )
    world.say(
        f"Instead, {hero.id} asked the miller to mend the old wall, and {twerp.id} to help carry stones until sunset."
    )
    world.say(
        f"So the village kept its peace, {treasure.label} was safe again, and the twerp learned that a trick can trip its own feet."
    )

    world.facts.update(
        hero=hero,
        twerp=twerp,
        treasure=treasure,
        place=place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    twerp = f["twerp"]
    treasure = f["treasure"]
    place = f["place"]
    return [
        f'Write a short folk tale about {hero.id}, {twerp.id}, and a missing {treasure.label} at {place.name}.',
        f"Tell a gentle village story where a twerp causes trouble, but a twist leads to a fair ending.",
        f'Write a child-friendly tale set in {place.name} that ends with {hero.id} getting back the {treasure.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    twerp = f["twerp"]
    treasure = f["treasure"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who was the child in the story?",
            answer=f"The child was {hero.id}, who lived near {place.name}.",
        ),
        QAItem(
            question=f"What did the twerp take?",
            answer=f"{twerp.id} took the {treasure.label}, which had belonged to {hero.id}.",
        ),
        QAItem(
            question=f"What was the twist in the tale?",
            answer=f"The twist came when {twerp.id} slipped on a root and the hidden {treasure.label} rolled into the open.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{hero.id} got the {treasure.label} back, and {twerp.id} had to help mend the damage.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a twerp?",
            answer="A twerp is a silly, unkind person who acts in a foolish way and often makes trouble.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what the reader expected.",
        ),
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is an old-style story passed from voice to voice, often with a lesson at the end.",
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
        if e.kind == "thing":
            bits.append(f"owner={e.owner}")
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


SETTINGS = {
    "village": PLACES["village"],
    "cottage": PLACES["cottage"],
    "wood": PLACES["wood"],
    "market": PLACES["market"],
}

PRIZES = {
    "bread": TREASURES["bread"],
    "bell": TREASURES["bell"],
    "cloak": TREASURES["cloak"],
    "ring": TREASURES["ring"],
}

CURATED = [
    StoryParams(place="village", hero_name="Mina", hero_type="girl", twerp_name="Snip", treasure="bread"),
    StoryParams(place="market", hero_name="Pip", hero_type="boy", twerp_name="Murk", treasure="bell"),
    StoryParams(place="wood", hero_name="Nell", hero_type="girl", twerp_name="Puck", treasure="cloak"),
]


ASP_RULES = r"""
% A treasure is taken when the twerp carries it.
taken(T) :- carries(T, Tp), twerp(Tp).

% A twist is present when a taken treasure is found again by the hero.
twist(H, T, Tp) :- hero(H), twerp(Tp), treasure(T), taken(T), found_again(H, T).

% A valid story has exactly one hero, one twerp, and one treasure in a place.
valid_story(P, H, Tp, T) :- place(P), hero(H), twerp(Tp), treasure(T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if place.old_magic:
            lines.append(asp.fact("old_magic", pid))
    for tid in TWERPS:
        lines.append(asp.fact("twerp", tid))
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for tr in PRIZES:
        lines.append(asp.fact("treasure", tr))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for p in SETTINGS:
        for h in HEROES:
            for t in TWERPS:
                for tr in PRIZES:
                    combos.append((p, h, t, tr))
    return combos


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    got = sorted(set(asp.atoms(model, "valid_story")))
    expected = sorted(set((p, h, t, tr) for p in SETTINGS for h in HEROES for t in TWERPS for tr in PRIZES))
    if got == expected:
        print(f"OK: clingo gate matches Python registry ({len(got)} combos).")
        return 0
    print("MISMATCH between clingo and Python registry:")
    print("  clingo only:", sorted(set(got) - set(expected)))
    print("  python only:", sorted(set(expected) - set(got)))
    return 1


HEROES = ["Mina", "Pip", "Nell", "Tob", "Ivy", "Finn"]
TWERPS = ["Snip", "Murk", "Wren", "Joss", "Brag", "Puck"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a folk tale with a twerp and a twist.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name", choices=HEROES)
    ap.add_argument("--twerp", choices=TWERPS)
    ap.add_argument("--treasure", choices=PRIZES.keys())
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    hero_name = args.name or rng.choice(HEROES)
    twerp_name = args.twerp or rng.choice(TWERPS)
    treasure = args.treasure or rng.choice(list(PRIZES.keys()))
    hero_type = "girl" if hero_name in {"Mina", "Nell", "Ivy"} else "boy"
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, twerp_name=twerp_name, treasure=treasure)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.hero_name, params.hero_type, params.twerp_name, params.treasure)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/4."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible story shapes:\n")
        for row in combos:
            print("  ", row)
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
