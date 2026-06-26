#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/moo_venom_blurt_conflict_sharing_suspense_fairy.py
===============================================================================================================

A tiny fairy-tale story world about a small enchanted meadow, a grumpy
serpent, a kind sharing choice, and a suspenseful rescue.

Seed tale sketch:
---
In a bright fairy meadow, a little cow named Miri loved to moo at the moon
and share warm milk with everyone. One day, a thorn-crowned snake hoarded a
bottle of venom and dared the moonlit brook to stop him. Miri blurted out
the snake's secret, which caused a conflict with the wood sprites, but the
little fairy who loved sharing found a brave way to soothe the snake, release
the milk, and keep the meadow safe.

World model:
---
- Characters have meters (health, hunger, fear, trust, kindness, venom, milk)
  and memes (hope, conflict, sharing, suspense, embarrassment).
- The tale begins with a peaceful shared feast.
- Suspense rises when the snake guards venom and the brook is trapped.
- Conflict peaks when the hero blurts the secret aloud.
- Sharing resolves the problem when milk is offered in return for help.
- The ending proves the change by showing the meadow calm again.
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
# Core data
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    helper: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "fairy", "queen", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "cow", "king", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the fairy meadow"
    detail: str = "under a silver moon"
    affords: set[str] = field(default_factory=lambda: {"sharing", "moo", "venom"})


@dataclass
class StoryParams:
    name: str
    helper: str
    place: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "meadow": Setting(place="the fairy meadow", detail="under a silver moon"),
    "brook": Setting(place="the moonlit brook", detail="beside singing reeds"),
    "orchard": Setting(place="the orchard glade", detail="near a pear tree lantern"),
}

HEROES = {
    "Miri": ("cow", "little cow"),
    "Lina": ("fairy", "little fairy"),
    "Toby": ("boy", "little boy"),
}

HELPERS = {
    "Pip": ("sparrow", "small sparrow"),
    "Nell": ("fairy", "kind fairy"),
    "Bram": ("rabbit", "round rabbit"),
}

# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_story(name: str, helper: str, place: str) -> bool:
    return name in HEROES and helper in HELPERS and place in SETTINGS


def explain_invalid(name: str, helper: str, place: str) -> str:
    return f"(No story: I can only tell fairy tales for known hero, helper, and place choices, but got {name!r}, {helper!r}, {place!r}.)"


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    if not valid_story(params.name, params.helper, params.place):
        raise StoryError(explain_invalid(params.name, params.helper, params.place))

    setting = SETTINGS[params.place]
    world = World(setting)

    hero_type, hero_phrase = HEROES[params.name]
    helper_type, helper_phrase = HELPERS[params.helper]

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=hero_type,
        label=params.name,
        phrase=hero_phrase,
        meters={"health": 3.0, "trust": 1.0, "kindness": 2.0, "milk": 1.0},
        memes={"hope": 2.0, "sharing": 1.0, "suspense": 0.0, "conflict": 0.0, "blurt": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type=helper_type,
        label=params.helper,
        phrase=helper_phrase,
        meters={"health": 2.0, "trust": 2.0, "kindness": 2.0},
        memes={"hope": 1.0, "sharing": 2.0, "suspense": 0.0},
    ))
    snake = world.add(Entity(
        id="snake",
        kind="character",
        type="snake",
        label="thorn-crowned snake",
        phrase="thorn-crowned snake",
        meters={"venom": 3.0, "health": 2.0, "fear": 2.0},
        memes={"suspense": 2.0, "conflict": 1.0},
    ))
    brook = world.add(Entity(
        id="brook",
        kind="thing",
        type="brook",
        label="moonlit brook",
        phrase="moonlit brook",
        meters={"water": 2.0},
        memes={"hope": 1.0},
    ))

    world.facts.update(hero=hero, helper=helper, snake=snake, brook=brook, place=setting)

    # Act 1: a peaceful beginning.
    world.say(
        f"In {setting.place}, {hero.label} loved to moo softly and share sweet milk with every little friend."
    )
    world.say(
        f"{helper.label} often skipped nearby, and together they laughed under {setting.detail}."
    )

    # Act 2: suspense and conflict.
    world.para()
    world.say(
        f"One evening, the thorn-crowned snake coiled beside the brook and hid a bottle of venom in the reeds."
    )
    hero.memes["suspense"] += 2.0
    snake.memes["suspense"] += 1.0
    world.say(
        f"{hero.label} noticed the glinting bottle and felt a hush fall over the meadow."
    )
    hero.memes["blurt"] += 1.0
    hero.memes["conflict"] += 1.0
    helper.memes["suspense"] += 1.0
    world.say(
        f"Then {hero.label} blurted the secret aloud: the snake had hidden the venom!"
    )
    world.say(
        f"The wood sprites gasped, and a sharp conflict fluttered through the grass."
    )

    # Act 3: sharing as the turn.
    world.para()
    helper.memes["sharing"] += 1.0
    hero.memes["sharing"] += 1.0
    hero.meters["milk"] += 1.0
    snake.meters["fear"] += 1.0
    world.say(
        f"{helper.label} gently asked {hero.label} to share a little milk instead of anger."
    )
    world.say(
        f"{hero.label} nodded, lifted a small pail, and shared the milk with the snake."
    )
    snake.memes["conflict"] = 0.0
    snake.meters["venom"] = 0.0
    brook.meters["water"] += 1.0
    hero.meters["trust"] += 1.0
    hero.memes["hope"] += 2.0
    world.say(
        f"The snake's tight coils loosened, the venom was put away, and the brook sparkled free."
    )
    world.say(
        f"By dawn, {hero.label} was mooing happily again, {helper.label} was smiling, and the meadow felt safe."
    )

    return world


# ---------------------------------------------------------------------------
# Q&A and prose helpers
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    place: Setting = f["place"]  # type: ignore[assignment]
    return [
        f'Write a short fairy tale for a child about {hero.label}, a mooing helper, and a secret in {place.place}.',
        f"Tell a gentle story where {hero.label} blurts out a hidden danger, but sharing helps the day end well.",
        f'Write a moonlit meadow story with the words "moo", "venom", and "blurt" in a magical, child-friendly way.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    snake: Entity = f["snake"]  # type: ignore[assignment]
    place: Setting = f["place"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who did the story follow in {place.place}?",
            answer=f"It followed {hero.label}, the little {hero.phrase}, and {helper.label}, who stayed close by.",
        ),
        QAItem(
            question="What secret did the hero blurt out?",
            answer=f"{hero.label} blurted out that the thorn-crowned snake had hidden venom in the reeds.",
        ),
        QAItem(
            question="How did the conflict end?",
            answer=f"The conflict ended when {hero.label} and {helper.label} shared milk, which calmed the snake and freed the brook.",
        ),
        QAItem(
            question=f"Why was there suspense in the meadow?",
            answer=f"There was suspense because the snake guarded venom beside the brook and everyone waited to see what would happen next.",
        ),
        QAItem(
            question=f"What changed by the end of the tale in {place.place}?",
            answer=f"By the end, the venom was put away, the brook was safe again, and {hero.label} was mooing happily.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cow known for saying?",
            answer="A cow is often known for mooing.",
        ),
        QAItem(
            question="What is venom?",
            answer="Venom is a poison made by some animals, like snakes, that can hurt if it gets into a body.",
        ),
        QAItem(
            question="What does it mean to blurt something out?",
            answer="To blurt something out means to say it suddenly without thinking first.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use or enjoy something with you.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of waiting anxiously to find out what will happen next.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:9}) meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Facts:
% hero(Name). helper(Name). place(Name). can_story(Name, Helper, Place).

% In this small world, a story is valid exactly when the named choices exist.
valid_story(H, K, P) :- hero(H), helper(K), place(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for name in HEROES:
        lines.append(asp.fact("hero", name))
    for name in HELPERS:
        lines.append(asp.fact("helper", name))
    for name in SETTINGS:
        lines.append(asp.fact("place", name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(h, k, p) for h in HEROES for k in HELPERS for p in SETTINGS}
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in asp:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# StorySample generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(sorted(HEROES))
    helper = args.helper or rng.choice(sorted(HELPERS))
    place = args.place or rng.choice(sorted(SETTINGS))
    if not valid_story(name, helper, place):
        raise StoryError(explain_invalid(name, helper, place))
    return StoryParams(name=name, helper=helper, place=place, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world: moo, venom, blurt, conflict, sharing, suspense.")
    ap.add_argument("--name", choices=sorted(HEROES))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--place", choices=sorted(SETTINGS))
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(f"{len(asp.atoms(model, 'valid_story'))} compatible stories:")
        for h, k, p in sorted(set(asp.atoms(model, "valid_story"))):
            print(f"  {h} + {k} + {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for h in sorted(HEROES):
            for k in sorted(HELPERS):
                for p in sorted(SETTINGS):
                    if valid_story(h, k, p):
                        params = StoryParams(name=h, helper=k, place=p, seed=base_seed)
                        samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(100, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
                params.seed = base_seed + i - 1
                sample = generate(params)
            except StoryError as err:
                print(str(err))
                return
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
