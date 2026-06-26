#!/usr/bin/env python3
"""
storyworlds/worlds/gerbil_fatso_surprise_fairy_tale.py
======================================================

A tiny fairy-tale storyworld about a gerbil, Fatso, and a surprise that must
be kept until the right moment.

Premise:
- A small gerbil wants to plan a surprise for a gentle friend called Fatso.
- The world tracks hiding, worry, and delight with meters and memes.
- The story turns when the surprise almost leaks early, then resolves when the
  reveal finally happens and everyone feels glad.

This world is intentionally small and constraint-checked: the surprise is only
reasonable in places that can hide it, and invalid explicit choices raise
StoryError.
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
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"gerbil", "mouse", "girl", "queen", "fairy"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king", "knight", "fox"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    can_hide: bool = False
    can_bake: bool = False


@dataclass
class Surprise:
    id: str
    kind: str
    reveal: str
    hiding_place: str
    secret_steps: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    surprise: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "burrow": Setting(place="the rabbit burrow", can_hide=True, can_bake=False),
    "glade": Setting(place="the moonlit glade", can_hide=True, can_bake=False),
    "cottage": Setting(place="the little cottage kitchen", can_hide=False, can_bake=True),
    "meadow": Setting(place="the flower meadow", can_hide=True, can_bake=False),
}

SURPRISES = {
    "berrypie": Surprise(
        id="berrypie",
        kind="berry pie",
        reveal="a warm berry pie",
        hiding_place="under a cloth",
        secret_steps=["gather berries", "mix the sweet filling", "bake it golden"],
        tags={"berry", "pie", "sweet"},
    ),
    "lantern": Surprise(
        id="lantern",
        kind="lantern",
        reveal="a tiny lantern with a star painted on it",
        hiding_place="behind a door",
        secret_steps=["fold the paper sides", "set in a candle", "tie on a ribbon"],
        tags={"light", "star", "glow"},
    ),
    "crown": Surprise(
        id="crown",
        kind="flower crown",
        reveal="a flower crown made of daisies",
        hiding_place="inside a basket",
        secret_steps=["pick daisies", "weave the stems", "nestle it safely"],
        tags={"flower", "daisy", "spring"},
    ),
}

HERO_NAMES = ["Pip", "Miri", "Tansy", "Lark", "Nim"]
FRIEND_NAMES = ["Fatso", "Puddle", "Bramble", "Moss", "Nettle"]
TRAITS = ["small", "brave", "gentle", "curious", "cheerful"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def setting_detail(setting: Setting) -> str:
    if setting.place == "the little cottage kitchen":
        return "The kettle sang softly, and the windows shone like honey."
    if setting.place == "the moonlit glade":
        return "The moon laid a silver path across the grass."
    if setting.place == "the rabbit burrow":
        return "The tunnels were snug, and the air smelled like warm earth."
    return "The flowers nodded in the breeze as if they knew a secret."


def can_hold_surprise(setting: Setting, surprise: Surprise) -> bool:
    if surprise.id == "berrypie":
        return setting.can_bake
    return setting.can_hide


def intro(world: World, hero: Entity, friend: Entity, surprise: Surprise) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    world.say(
        f"Once upon a time, there was a little {hero.traits[0]} {hero.type} named {hero.id}."
    )
    world.say(
        f"{hero.id} loved {friend.id}, who everyone called {friend.label}, and one day {hero.id} decided to make a surprise."
    )
    world.say(setting_detail(world.setting))


def plan(world: World, hero: Entity, surprise: Surprise) -> None:
    world.say(
        f"{hero.id} tiptoed about and began to {', then '.join(surprise.secret_steps)}."
    )
    hero.meters["secret"] = hero.meters.get("secret", 0) + 1
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1


def suspicion(world: World, friend: Entity, hero: Entity) -> None:
    friend.memes["curiosity"] = friend.memes.get("curiosity", 0) + 1
    world.say(
        f"Fatso sniffed the air and blinked. \"What are you hiding, little friend?\" {friend.id} asked."
    )
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1


def near_leak(world: World, hero: Entity, surprise: Surprise) -> None:
    world.say(
        f"{hero.id}'s heart went thump-thump, because one tiny crumb nearly fell from the {surprise.hiding_place}."
    )
    hero.memes["fear"] = hero.memes.get("fear", 0) + 1


def reveal(world: World, hero: Entity, friend: Entity, surprise: Surprise) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0) + 1
    friend.memes["surprise"] = friend.memes.get("surprise", 0) + 1
    world.say(
        f"Then the big moment came. {hero.id} opened the hiding place and showed {friend.id} {surprise.reveal}."
    )
    world.say(
        f"Fatso gasped, then smiled so wide that the whole glade seemed to glow."
    )


def ending(world: World, hero: Entity, friend: Entity, surprise: Surprise) -> None:
    world.say(
        f"{friend.id} laughed and thanked {hero.id}, and soon they were sharing the happy surprise together."
    )
    world.say(
        f"By the end of the day, the secret was no longer a secret, and it had turned into a memory they both loved."
    )


def tell(setting: Setting, surprise: Surprise, hero_name: str, hero_type: str,
         friend_name: str, friend_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["small", "gentle"]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, label="Fatso", traits=["kind", "round"]))
    world.facts["surprise"] = surprise
    world.facts["hero"] = hero
    world.facts["friend"] = friend

    intro(world, hero, friend, surprise)
    world.para()
    plan(world, hero, surprise)
    if surprise.id == "berrypie":
        world.say("The pie smelled so sweet that even the bees seemed to pause and listen.")
    if setting.can_hide:
        suspicion(world, friend, hero)
        near_leak(world, hero, surprise)
    world.para()
    reveal(world, hero, friend, surprise)
    ending(world, hero, friend, surprise)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    surprise: Surprise = f["surprise"]
    return [
        f"Write a fairy tale about a {hero.type} named {hero.id} who plans a surprise for Fatso.",
        f"Tell a child-friendly story where {hero.id} keeps {surprise.kind} secret until the end.",
        f"Write a gentle fairy tale with a little gerbil, a friend called Fatso, and a happy surprise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    surprise: Surprise = f["surprise"]
    return [
        QAItem(
            question=f"Who was the little {hero.type} in the story?",
            answer=f"The little {hero.type} was {hero.id}, and {hero.id} wanted to make a surprise for Fatso.",
        ),
        QAItem(
            question=f"What was the surprise?",
            answer=f"The surprise was {surprise.reveal}. {hero.id} kept it hidden until the right moment.",
        ),
        QAItem(
            question="How did Fatso feel when the surprise was revealed?",
            answer="Fatso felt very happy and surprised, and the whole moment turned joyful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something kept secret for a little while so another person can find it at the right moment.",
        ),
        QAItem(
            question="Why do people hide gifts before giving them?",
            answer="People hide gifts first so the gift stays secret until the happy reveal.",
        ),
        QAItem(
            question="What is a gerbil?",
            answer="A gerbil is a small furry animal with quick feet and a long tail.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/2.

valid(Surprise, Setting) :- surprise(Surprise), setting(Setting), can_hold(Setting, Surprise).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.can_hide:
            lines.append(asp.fact("can_hide", sid))
        if s.can_bake:
            lines.append(asp.fact("can_bake", sid))
    for rid, r in SURPRISES.items():
        lines.append(asp.fact("surprise", rid))
        if r.id == "berrypie":
            lines.append(asp.fact("requires", rid, "baking"))
        else:
            lines.append(asp.fact("requires", rid, "hiding"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def python_valid() -> list[tuple]:
    return sorted(
        (sid, setting)
        for sid, surprise in SURPRISES.items()
        for setting, s in SETTINGS.items()
        if can_hold_surprise(s, surprise)
    )


def asp_verify() -> int:
    a = set(asp_valid())
    b = set(python_valid())
    if a == b:
        print(f"OK: ASP matches Python ({len(a)} valid pairs).")
        return 0
    print("MISMATCH:")
    if a - b:
        print(" only in ASP:", sorted(a - b))
    if b - a:
        print(" only in Python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld: a gerbil, Fatso, and a surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", default="gerbil")
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", default="fatso")
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
    surprise = args.surprise or rng.choice(list(SURPRISES))
    if not can_hold_surprise(SETTINGS[setting], SURPRISES[surprise]):
        raise StoryError("That surprise does not fit this setting in a fairytale way.")
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    friend_name = args.friend_name or "Fatso"
    return StoryParams(
        setting=setting,
        surprise=surprise,
        hero_name=hero_name,
        hero_type=args.hero_type,
        friend_name=friend_name,
        friend_type=args.friend_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SURPRISES[params.surprise],
                 params.hero_name, params.hero_type, params.friend_name, params.friend_type)
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
        lines.append(
            f"  {e.id:10} type={e.type:8} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} valid setting/surprise pairs:")
        for pair in vals:
            print(" ", pair)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("cottage", "berrypie", "Pip", "gerbil", "Fatso", "fatso"),
            StoryParams("meadow", "crown", "Miri", "gerbil", "Fatso", "fatso"),
            StoryParams("glade", "lantern", "Tansy", "gerbil", "Fatso", "fatso"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
