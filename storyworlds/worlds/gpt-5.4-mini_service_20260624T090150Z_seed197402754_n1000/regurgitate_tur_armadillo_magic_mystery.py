#!/usr/bin/env python3
"""
storyworlds/worlds/regurgitate_tur_armadillo_magic_mystery.py
==============================================================

A small mystery storyworld with a magical armadillo, a strange tur, and a
clue trail that can be examined, mistaken, and finally understood.

Seed-tale premise:
---
An armadillo named Arlo finds a shiny tur in the garden path. The tur is
magic, but nobody knows what it does. When Arlo gets nervous, he regurgitates
a tiny clue: a pebble, a ribbon, then a leaf. His friend Mira thinks the clues
might point to the owner of the tur. They follow the hints through the yard and
discover that the tur is a toy whistle that was lost by the neighbor child.
Arlo keeps the whistle safe and everyone laughs when the mystery is solved.
---

This script turns that premise into a small stateful simulation:
- The armadillo can be curious, nervous, proud, or relieved.
- The magical tur can shimmer, hide, and trigger clues.
- Regurgitated clues are physical objects with meaning.
- The ending depends on whether the mystery is solved and whether the tur is
  returned safely.

The prose is generated from simulated state, not from a frozen template.
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
# World entities and state
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden: bool = False
    magical: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.type

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the garden"
    indoors: bool = False
    weather: str = "misty"


@dataclass
class Mystery:
    name: str
    clue_kind: str
    reveal: str
    hiding_place: str
    magic_effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero_name: str
    friend_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "garden": Setting(place="the garden", indoors=False, weather="misty"),
    "backyard": Setting(place="the backyard", indoors=False, weather="soft and gray"),
    "porch": Setting(place="the porch", indoors=False, weather="drizzly"),
}

MYSTERIES = {
    "whistle": Mystery(
        name="whistle",
        clue_kind="sound",
        reveal="a toy whistle",
        hiding_place="under a flower pot",
        magic_effect="it gave a tiny trilling note when touched by moonlight",
        tags={"sound", "toy", "magic", "mystery"},
    ),
    "jar": Mystery(
        name="jar",
        clue_kind="glow",
        reveal="a glowing jar lid",
        hiding_place="behind a watering can",
        magic_effect="it glowed when a friendly paw got close",
        tags={"glow", "glass", "magic", "mystery"},
    ),
    "key": Mystery(
        name="key",
        clue_kind="shine",
        reveal="a silver key",
        hiding_place="under the porch step",
        magic_effect="it shone when someone said 'please'",
        tags={"shine", "metal", "magic", "mystery"},
    ),
}

GIRL_NAMES = ["Mira", "Luna", "Nina", "Zoe", "Ava"]
BOY_NAMES = ["Arlo", "Finn", "Theo", "Noah", "Leo"]

TRAITS = ["curious", "careful", "brave", "gentle", "smart"]


# ---------------------------------------------------------------------------
# ASP twin and facts
# ---------------------------------------------------------------------------
ASP_RULES = r"""
mystery(X) :- item(X).
magical(X) :- magic_item(X).
needs_clue(X) :- mystery(X), magical(X).
solved(X) :- clue(X), reveal(X).
good_story(P, M) :- place(P), mystery_item(M), needs_clue(M), solved(M).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("item", mid))
        lines.append(asp.fact("mystery_item", mid))
        lines.append(asp.fact("reveal", mid))
        lines.append(asp.fact("clue_kind", mid, m.clue_kind))
        if "magic" in m.tags:
            lines.append(asp.fact("magic_item", mid))
        lines.append(asp.fact("hiding_place", mid, m.hiding_place))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show good_story/2."))
    clingo_set = set(asp.atoms(model, "good_story"))
    python_set = {(place, mid) for place in SETTINGS for mid in MYSTERIES}
    if clingo_set == python_set:
        print(f"OK: ASP gate matches Python registry ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if clingo_set - python_set:
        print("  only in ASP:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in Python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A magical armadillo mystery with regurgitated clues."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
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


def valid_combos() -> list[tuple[str, str]]:
    return [(place, mid) for place in SETTINGS for mid in MYSTERIES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        (place, mid)
        for place, mid in valid_combos()
        if (args.place is None or place == args.place)
        and (args.mystery is None or mid == args.mystery)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mid = rng.choice(sorted(combos))
    hero = args.hero_name or rng.choice(GIRL_NAMES + BOY_NAMES)
    friend = args.friend_name or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero])
    return StoryParams(place=place, mystery=mid, hero_name=hero, friend_name=friend)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m: Mystery = f["mystery"]  # type: ignore[assignment]
    hero: Entity = f["hero"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    return [
        f'Write a short mystery story for a child that includes the word "regurgitate" and the magical item "{m.name}".',
        f"Tell a gentle story where {hero.id} the armadillo and {friend.id} follow clues to solve a magic mystery.",
        f'Write a tiny story about an armadillo who regurgitates clues when nervous and learns what the tur was for.',
    ]


def _regurgitate(world: World, hero: Entity, clue: str) -> None:
    hero.memes["nervous"] = hero.memes.get("nervous", 0) + 1
    world.say(f"{hero.id} felt a flutter in {hero.pronoun('possessive')} belly and had to regurgitate a {clue}.")

def _magic_twist(world: World, mystery: Mystery) -> None:
    world.say(f"The {mystery.name} gave off a small magic shimmer; {mystery.magic_effect}.")

def _investigate(world: World, hero: Entity, friend: Entity, mystery: Mystery) -> None:
    hero.memes["curious"] = hero.memes.get("curious", 0) + 1
    friend.memes["curious"] = friend.memes.get("curious", 0) + 1
    world.say(f"{friend.id} bent close and studied the clue trail with {hero.id}.")
    world.say(f"They followed it toward {mystery.hiding_place}.")

def _reveal(world: World, hero: Entity, friend: Entity, mystery: Mystery, item: Entity) -> None:
    item.hidden = False
    item.carried_by = hero.id
    hero.memes["relieved"] = hero.memes.get("relieved", 0) + 1
    friend.memes["happy"] = friend.memes.get("happy", 0) + 1
    world.say(f"At last, they found {mystery.reveal}.")
    world.say(f"{hero.id} kept it safe while {friend.id} smiled, because the mystery was finally solved.")

def tell(setting: Setting, mystery: Mystery, hero_name: str, friend_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="armadillo", label="armadillo"))
    friend = world.add(Entity(id=friend_name, kind="character", type="girl", label="friend"))
    item = world.add(Entity(
        id="tur",
        kind="thing",
        type="tur",
        label="tur",
        phrase=f"a small magical {mystery.name}",
        hidden=True,
        magical=True,
    ))

    world.facts.update(hero=hero, friend=friend, mystery=mystery, item=item)

    world.say(f"One misty morning in {setting.place}, {hero.id} found a curious tur by a path of wet leaves.")
    world.say(f"It was no ordinary trinket. The tur looked magical, and that made {hero.id} even more curious.")
    _magic_twist(world, mystery)

    world.para()
    world.say(f"Then the mystery began.")
    _regurgitate(world, hero, "pebble")
    _regurgitate(world, hero, "ribbon")
    _regurgitate(world, hero, "leaf")
    world.say(f"Each clue made {friend.id} think harder about where the tur had come from.")
    _investigate(world, hero, friend, mystery)

    world.para()
    _reveal(world, hero, friend, mystery, item)
    world.say(f"In the end, {hero.id} carried the {mystery.name} home, and the little yard felt calm again.")
    world.facts["solved"] = True
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MYSTERIES[params.mystery], params.hero_name, params.friend_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    mystery: Mystery = world.facts["mystery"]  # type: ignore[assignment]
    item: Entity = world.facts["item"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What did {hero.id} find in {world.setting.place}?",
            answer=f"{hero.id} found a magical {mystery.name} in {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} do when {hero.id} got nervous?",
            answer=f"{hero.id} regurgitated clues, like a pebble, a ribbon, and a leaf.",
        ),
        QAItem(
            question=f"How did {friend.id} help solve the mystery?",
            answer=f"{friend.id} studied the clues with {hero.id} and followed them to {mystery.hiding_place}.",
        ),
        QAItem(
            question=f"What was the tur really?",
            answer=f"The tur was {mystery.reveal}, and {hero.id} kept it safe at the end.",
        ),
        QAItem(
            question=f"Why did the story feel like a mystery?",
            answer=f"It felt like a mystery because nobody knew what the tur was for at first, and the clue trail had to be followed before the answer was revealed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an armadillo?",
            answer="An armadillo is a small animal with a hard shell on its back that helps protect it.",
        ),
        QAItem(
            question="What does regurgitate mean?",
            answer="Regurgitate means to bring food or something else back up from the stomach or belly.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle or secret that people do not understand yet.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic means something surprising or special happens that does not work like ordinary things do.",
        ),
    ]


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
        bits = []
        if e.hidden:
            bits.append("hidden=True")
        if e.magical:
            bits.append("magical=True")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden", mystery="whistle", hero_name="Arlo", friend_name="Mira"),
    StoryParams(place="backyard", mystery="jar", hero_name="Finn", friend_name="Luna"),
    StoryParams(place="porch", mystery="key", hero_name="Theo", friend_name="Nina"),
]


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show good_story/2."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify_runner() -> int:
    combos = set(asp_valid_combos())
    py = {(place, mid) for place in SETTINGS for mid in MYSTERIES}
    if combos == py:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if combos - py:
        print("  only in ASP:", sorted(combos - py))
    if py - combos:
        print("  only in Python:", sorted(py - combos))
    return 1


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
        print(asp_program("#show good_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify_runner())
    if args.asp:
        import asp

        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for place, mystery in combos:
            print(f"  {place:10} {mystery}")
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
            header = f"### {p.hero_name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def story_knowledge_tags(world: World) -> set[str]:
    mystery: Mystery = world.facts["mystery"]  # type: ignore[assignment]
    return set(mystery.tags) | {"armadillo", "regurgitate"}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = story_knowledge_tags(world)
    qa = [
        QAItem(
            question="What is an armadillo?",
            answer="An armadillo is a small animal with a hard shell on its back that helps protect it.",
        ),
        QAItem(
            question="What does regurgitate mean?",
            answer="Regurgitate means to bring food or something else back up from the stomach or belly.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle or secret that people do not understand yet.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic means something surprising or special happens that does not work like ordinary things do.",
        ),
    ]
    # Keep only the questions relevant to this world, but always include the core trio.
    return qa if "mystery" in tags else qa[:3]


if __name__ == "__main__":
    main()
