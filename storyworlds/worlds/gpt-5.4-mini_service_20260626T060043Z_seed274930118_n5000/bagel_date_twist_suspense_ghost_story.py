#!/usr/bin/env python3
"""
storyworlds/worlds/bagel_date_twist_suspense_ghost_story.py
===========================================================

A small ghost-story world with a bagel, a date, suspense, and a twist.

Seed image:
---
A child goes into an old bakery at night to fetch a bagel with date filling.
The lights flicker, the shelves creak, and a ghostly shape seems to follow
them through the dark. At the end, the scare turns into a surprise: the ghost
is lonely, hungry, and only wanted a warm bagel date snack.

This file builds that premise as a tiny stateful simulation with meters
(hunger, fear, glow, crumbs) and memes (worry, relief, curiosity).
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the old bakery"
    indoor: bool = True
    dark: bool = True


@dataclass
class Bagel:
    label: str
    phrase: str
    filling: str
    warm: bool = True
    sweet: bool = True


@dataclass
class GhostMood:
    label: str
    trait: str
    surprise: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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


def _hero_name_pool(gender: str) -> list[str]:
    return ["Maya", "Lina", "Nora", "Ava", "Milo", "Theo", "Owen", "Finn"] if gender == "any" else (
        ["Maya", "Lina", "Nora", "Ava"] if gender == "girl" else ["Milo", "Theo", "Owen", "Finn"]
    )


SETTINGS = {
    "bakery": Setting(place="the old bakery", indoor=True, dark=True),
    "kitchen": Setting(place="the sleepy kitchen", indoor=True, dark=True),
    "porch": Setting(place="the porch by the pantry", indoor=False, dark=True),
}

BAGELS = {
    "plain": Bagel(label="bagel", phrase="a warm bagel", filling="", warm=True, sweet=False),
    "date": Bagel(label="date bagel", phrase="a warm bagel with date filling", filling="date", warm=True, sweet=True),
    "toasted": Bagel(label="toasted bagel", phrase="a toasted bagel with sweet date spread", filling="date", warm=True, sweet=True),
}

GHOSTS = {
    "shy": GhostMood(label="ghost", trait="shy", surprise="wanted a snack"),
    "lonely": GhostMood(label="ghost", trait="lonely", surprise="was only looking for company"),
    "hungry": GhostMood(label="ghost", trait="hungry", surprise="smelled the sweet date filling"),
}

TRAITS = ["curious", "quiet", "brave", "sleepy", "gentle"]


@dataclass
class StoryParams:
    setting: str
    bagel: str
    ghost: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(setting="bakery", bagel="date", ghost="hungry", name="Maya", gender="girl", trait="curious"),
    StoryParams(setting="kitchen", bagel="toasted", ghost="lonely", name="Theo", gender="boy", trait="brave"),
    StoryParams(setting="porch", bagel="date", ghost="shy", name="Nora", gender="girl", trait="gentle"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for b in BAGELS:
            for g in GHOSTS:
                combos.append((s, b, g))
    return combos


def explain_rejection(setting: str, bagel: str, ghost: str) -> str:
    return f"(No story: the combination {setting}/{bagel}/{ghost} is not reasonable for this ghost-bagel tale.)"


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.gender == "girl" else "boy",
        meters={"fear": 0.0, "hunger": 1.0, "curiosity": 1.0},
        memes={"worry": 0.0, "relief": 0.0, "courage": 0.0},
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="ghost",
        type="ghost",
        label="the ghost",
        meters={"glow": 0.5, "hunger": 0.5, "float": 1.0},
        memes={"loneliness": 1.0, "worry": 0.0},
    ))
    bagel = world.add(Entity(
        id="bagel",
        kind="thing",
        type="food",
        label="bagel",
        phrase=BAGELS[params.bagel].phrase,
        owner=hero.id,
        meters={"warmth": 1.0, "crumbs": 0.2},
        memes={"tempting": 1.0},
    ))
    lantern = world.add(Entity(
        id="lantern",
        kind="thing",
        type="light",
        label="lantern",
        phrase="a small lantern",
        meters={"glow": 1.0},
    ))
    world.facts.update(hero=hero, ghost=ghost, bagel=bagel, lantern=lantern, params=params)
    return world


def tell(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    ghost: Entity = f["ghost"]
    bagel: Entity = f["bagel"]
    params: StoryParams = f["params"]
    setting = world.setting

    hero.memes["courage"] += 0.5
    world.say(
        f"{hero.id} was a little {params.trait} {hero.type} who liked quiet nights and warm snacks."
    )
    world.say(
        f"One night, {hero.id} went to {setting.place} to get {bagel.phrase}."
    )
    world.say(
        f"The air felt cold, and the lantern made tiny yellow pools of light."
    )

    world.para()
    hero.meters["fear"] += 1.0
    hero.memes["worry"] += 1.0
    ghost.meters["glow"] += 0.5
    world.say(
        f"Then the shelves creaked. A soft white shape drifted past the flour jars, and {hero.id} froze."
    )
    world.say(
        f"{hero.id} held the lantern tighter, and every little sound seemed bigger in the dark."
    )

    world.para()
    if params.ghost == "hungry":
        ghost.meters["hunger"] += 1.0
    elif params.ghost == "lonely":
        ghost.memes["loneliness"] += 0.5
    else:
        ghost.memes["worry"] += 0.5

    world.say(
        f"The ghost floated closer, and {hero.id} almost ran. But the ghost stopped by the bagel box instead."
    )
    world.say(
        f'"I am not here to scare you," the ghost whispered. "I smelled the {bagel.phrase}."'
    )

    world.para()
    hero.meters["fear"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["relief"] += 1.0
    ghost.memes["loneliness"] += 0.5
    bagel.meters["crumbs"] += 0.5
    world.say(
        f"{hero.id} blinked. That was the twist: the ghost was not mean at all."
    )
    world.say(
        f"{hero.id} shared the {bagel.label}, and the ghost's pale face turned bright and happy."
    )
    world.say(
        f"Together they sat in the warm circle of lantern light, and the spooky bakery felt friendly at last."
    )

    world.facts["resolved"] = True
    world.facts["twist"] = True
    world.facts["suspense"] = True


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]
    bagel = BAGELS[params.bagel]
    ghost = GHOSTS[params.ghost]
    return [
        f'Write a short ghost story for a small child that includes "{bagel.label}" and a twist.',
        f"Tell a suspenseful story in {SETTINGS[params.setting].place} where {params.name} finds a {ghost.label} and shares a snack.",
        f'Write a gentle spooky story where the scary part turns into a surprise about a {bagel.filling or "plain"} bagel.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    ghost: Entity = f["ghost"]
    bagel: Entity = f["bagel"]
    params: StoryParams = f["params"]
    qa = [
        QAItem(
            question=f"Where did {hero.id} go at night?",
            answer=f"{hero.id} went to {SETTINGS[params.setting].place} to get {bagel.phrase}.",
        ),
        QAItem(
            question=f"What first made the story feel scary?",
            answer="The shelves creaked and a pale ghostly shape drifted through the dark, which made the night feel full of suspense.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that the ghost was not there to scare {hero.id}; it only wanted the {bagel.label} and some company.",
        ),
        QAItem(
            question=f"What did {hero.id} do at the end?",
            answer=f"{hero.id} shared the {bagel.label} with the ghost, and the bakery felt warm and friendly again.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = f["params"]
    bagel = BAGELS[params.bagel]
    out = [
        QAItem(
            question="What is a bagel?",
            answer="A bagel is a round bread roll with a hole in the middle. It can be plain or have a filling or spread.",
        ),
        QAItem(
            question="What is a date in food?",
            answer="A date is a sweet fruit. People often chop it up or mash it into a sticky filling for snacks and desserts.",
        ),
        QAItem(
            question="What does suspense mean in a story?",
            answer="Suspense means the story makes you wonder what will happen next and keeps you waiting to find out.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise that changes what you thought was going on.",
        ),
    ]
    if bagel.filling:
        out.append(
            QAItem(
                question="Why can a date filling taste sweet?",
                answer="Dates are naturally sweet, so a bagel with date filling can taste soft, sticky, and sweet.",
            )
        )
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
bagel_story(S, B, G) :- setting(S), bagel(B), ghost(G).
twist(S, B, G) :- bagel_story(S, B, G), spooky(S).
suspense(S) :- setting(S), spooky(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        if SETTINGS[sid].dark:
            lines.append(asp.fact("spooky", sid))
    for bid in BAGELS:
        lines.append(asp.fact("bagel", bid))
    for gid in GHOSTS:
        lines.append(asp.fact("ghost", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show bagel_story/3. #show twist/3. #show suspense/1."))
    return sorted(set(asp.atoms(model, "bagel_story")))


def asp_verify() -> int:
    import asp
    py = set((s, b, g) for s, b, g in valid_combos())
    cl = set(valid_combos_asp())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, b, g) for s in SETTINGS for b in BAGELS for g in GHOSTS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny ghost story with a bagel, a date, suspense, and a twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--bagel", choices=BAGELS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.bagel is None or c[1] == args.bagel)
              and (args.ghost is None or c[2] == args.ghost)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, bagel, ghost = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(_hero_name_pool(gender))
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, bagel=bagel, ghost=ghost, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
        print(asp_program("#show bagel_story/3. #show twist/3. #show suspense/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show bagel_story/3. #show twist/3. #show suspense/1."))
        print("bagel_story:", sorted(set(asp.atoms(model, "bagel_story"))))
        print("twist:", sorted(set(asp.atoms(model, "twist"))))
        print("suspense:", sorted(set(asp.atoms(model, "suspense"))))
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
            header = f"### {p.name}: {p.setting} / {p.bagel} / {p.ghost}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
