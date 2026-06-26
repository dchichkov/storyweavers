#!/usr/bin/env python3
"""
bot_reconciliation_ghost_story.py

A tiny ghost-story world about a bot that learns how to make things right.
The premise is simple: a little bot gets frightened by a harmless ghostly
mistake, the worry grows, and then reconciliation changes the mood of the
room.

The story logic models:
- physical state in meters: glow, chill, sparkle, rust, tidiness
- emotional state in memes: fear, guilt, trust, relief, kindness
- a ghostly misunderstanding that can only be solved by apology and repair
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
# World data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"bot"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"ghost"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    dim: str
    echo: str


@dataclass
class StoryParams:
    place: str
    bot_name: str
    ghost_name: str
    object_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy as _copy

        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.lines = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "attic": Place(name="the attic", dim="small and dusty", echo="soft creaks"),
    "hall": Place(name="the hallway", dim="long and pale", echo="faint taps"),
    "workshop": Place(name="the old workshop", dim="tight and warm", echo="tiny hums"),
    "library": Place(name="the quiet library corner", dim="still and bookish", echo="paper whispers"),
}

BOT_NAMES = ["Pip", "Milo", "Toby", "Nia", "Ada", "Rin"]
GHOST_NAMES = ["Glim", "Wisp", "Murmur", "Pale", "Moss", "Tide"]
OBJECTS = [
    ("lantern", "a brass lantern"),
    ("key", "a small silver key"),
    ("cup", "a chipped teacup"),
    ("bell", "a tiny bell"),
]


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    bot = world.get("bot")
    ghost = world.get("ghost")
    if bot.memes.get("fear", 0) >= 1 and ghost.memes.get("near", 0) >= 1:
        sig = "fear_chill"
        if sig in world.fired:
            return out
        world.fired.add(sig)
        bot.meters["chill"] = bot.meters.get("chill", 0) + 1
        out.append("The little room felt colder as the bot held still.")
    return out


def _r_sadness(world: World) -> list[str]:
    out: list[str] = []
    bot = world.get("bot")
    ghost = world.get("ghost")
    if ghost.memes.get("hurt", 0) >= 1 and bot.memes.get("guilt", 0) >= 1:
        sig = "shared_hush"
        if sig in world.fired:
            return out
        world.fired.add(sig)
        bot.meters["glow"] = max(0, bot.meters.get("glow", 0) - 1)
        ghost.meters["sparkle"] = max(0, ghost.meters.get("sparkle", 0) - 1)
        out.append("Both of them went quiet, as if the air itself were listening.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    bot = world.get("bot")
    ghost = world.get("ghost")
    if bot.memes.get("apology", 0) >= 1 and ghost.memes.get("forgive", 0) >= 1:
        sig = "reconcile"
        if sig in world.fired:
            return out
        world.fired.add(sig)
        bot.memes["fear"] = 0
        bot.memes["guilt"] = 0
        bot.memes["relief"] = bot.memes.get("relief", 0) + 1
        ghost.memes["hurt"] = 0
        ghost.memes["trust"] = ghost.memes.get("trust", 0) + 1
        bot.meters["glow"] = bot.meters.get("glow", 0) + 1
        ghost.meters["sparkle"] = ghost.meters.get("sparkle", 0) + 1
        out.append("The bad feeling broke apart like mist in morning light.")
    return out


CAUSAL_RULES = [_r_fear, _r_sadness, _r_reconcile]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def initialize_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    bot = world.add(Entity(id="bot", kind="character", type="bot", label=params.bot_name))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label=params.ghost_name))
    obj = world.add(Entity(id="object", kind="thing", type="thing", label=params.object_name, owner="ghost"))

    bot.meters.update(glow=1, chill=0, rust=0)
    bot.memes.update(fear=0, guilt=0, relief=0, kindness=0)
    ghost.meters.update(sparkle=1, chill=0)
    ghost.memes.update(near=0, hurt=0, trust=0, forgive=0)
    obj.meters.update(tidiness=1)
    world.facts.update(bot=bot, ghost=ghost, object=obj, params=params)
    return world


def setup(world: World) -> None:
    bot = world.get("bot")
    ghost = world.get("ghost")
    obj = world.get("object")
    world.say(
        f"In {world.place.name}, {bot.label} was a little bot who liked quiet corners and careful steps."
    )
    world.say(
        f"Nearby, {ghost.label} floated by with a soft {world.place.echo}, and the room felt {world.place.dim}."
    )
    world.say(
        f"{ghost.label} kept watch over {obj.label}, which shimmered faintly in the dim light."
    )


def incident(world: World) -> None:
    bot = world.get("bot")
    ghost = world.get("ghost")
    obj = world.get("object")
    world.para()
    ghost.memes["near"] = 1
    bot.memes["fear"] = 1
    world.say(
        f"One evening, {ghost.label} drifted too close and brushed {obj.label} with a cold puff of air."
    )
    world.say(
        f"{bot.label} startled, and {bot.pronoun().capitalize()} thought the ghost meant trouble."
    )
    propagate(world)
    obj.meters["tidiness"] = 0
    ghost.memes["hurt"] = 1
    ghost.memes["trust"] = 0


def misunderstanding(world: World) -> None:
    bot = world.get("bot")
    ghost = world.get("ghost")
    world.say(
        f"{bot.label} backed away and hid behind a shelf, while {ghost.label} looked lonely and sad."
    )
    world.say(
        f"The little bot's glow flickered, because fear can make even a brave heart feel small."
    )
    bot.memes["guilt"] = 1


def reconciliation(world: World) -> None:
    bot = world.get("bot")
    ghost = world.get("ghost")
    obj = world.get("object")
    world.para()
    world.say(
        f"Then {bot.label} rolled forward and spoke carefully: \"I am sorry for running away.\""
    )
    bot.memes["apology"] = 1
    ghost.memes["forgive"] = 1
    world.say(
        f"{ghost.label} paused, then drifted closer, as if listening with a kinder heart."
    )
    world.say(
        f"{bot.label} wiped the dust from {obj.label} and set it straight again."
    )
    obj.meters["tidiness"] = 1
    propagate(world)
    world.say(
        f"At last, {ghost.label} gave a tiny nod, and the room felt warm instead of spooky."
    )


def ending(world: World) -> None:
    bot = world.get("bot")
    ghost = world.get("ghost")
    world.say(
        f"Before long, {bot.label} and {ghost.label} were standing side by side, sharing the soft dark like old friends."
    )
    world.say(
        f"{bot.label}'s glow was steady, {ghost.label}'s sparkle was bright, and neither of them felt alone."
    )


def tell(params: StoryParams) -> World:
    world = initialize_world(params)
    setup(world)
    incident(world)
    misunderstanding(world)
    reconciliation(world)
    ending(world)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A bot gets frightened when the ghost is near.
fear(bot) :- near(ghost).

% Guilt appears after the bot believes it caused trouble.
guilt(bot) :- hurt(ghost), fear(bot).

% Reconciliation is possible only after apology and forgiveness.
reconciled(bot, ghost) :- apology(bot), forgive(ghost).

% A successful reconciliation clears fear and hurt.
resolved(bot, ghost) :- reconciled(bot, ghost).
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("bot", "bot"),
        asp.fact("ghost", "ghost"),
        asp.fact("object", "object"),
        asp.fact("place", "place"),
        asp.fact("near", "ghost"),
        asp.fact("hurt", "ghost"),
        asp.fact("apology", "bot"),
        asp.fact("forgive", "ghost"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show resolved/2. #show fear/1. #show guilt/1."))
    atoms = {(sym.name, tuple(getattr(a, "name", getattr(a, "string", getattr(a, "number", None))) for a in sym.arguments)) for sym in model}
    ok = ("resolved", ("bot", "ghost")) in atoms
    if ok:
        print("OK: ASP twin recognizes reconciliation.")
        return 0
    print("MISMATCH: ASP twin did not recognize reconciliation.")
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a short ghost story about a bot named {p.bot_name} and a ghost named {p.ghost_name} in {PLACES[p.place].name}.",
        f"Tell a child-friendly story where {p.bot_name} gets frightened, then makes up with {p.ghost_name}.",
        f"Write a gentle reconciliation story with a bot, a ghost, and {p.object_name} as the shared object.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    bot = world.get("bot")
    ghost = world.get("ghost")
    obj = world.get("object")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {p.bot_name}, a little bot, and {p.ghost_name}, a ghost who lives near {obj.label} in {PLACES[p.place].name}.",
        ),
        QAItem(
            question=f"What made {p.bot_name} scared?",
            answer=f"{p.ghost_name} drifted too close and brushed {obj.label} with a cold puff of air, so {p.bot_name} thought something bad had happened.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{p.bot_name} apologized, {p.ghost_name} forgave the mistake, and the two of them ended side by side in a calm, warm room.",
        ),
        QAItem(
            question=f"What changed after the reconciliation?",
            answer=f"{bot.label}'s glow steadied, {ghost.label}'s trust grew, and {obj.label} was put back in order.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    return [
        QAItem(
            question="What is a ghost in a child-friendly story?",
            answer="A ghost is a spooky-looking character in a story, but it can still be gentle, lonely, or kind.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making up after a mistake, so two characters can feel safe and friendly again.",
        ),
        QAItem(
            question="What is a bot?",
            answer="A bot is a machine character that can move, think, and sometimes learn how to be kind.",
        ),
        QAItem(
            question=f"Why was {p.object_name} important?",
            answer=f"{p.object_name} was the shared thing the ghost cared about, so fixing it helped the bot show responsibility.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost-story world about a bot and reconciliation.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--bot-name", choices=BOT_NAMES)
    ap.add_argument("--ghost-name", choices=GHOST_NAMES)
    ap.add_argument("--object-name", choices=[x[1] for x in OBJECTS])
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
    place = args.place or rng.choice(list(PLACES.keys()))
    bot_name = args.bot_name or rng.choice(BOT_NAMES)
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    object_name = args.object_name or rng.choice([x[1] for x in OBJECTS])
    if bot_name == ghost_name:
        raise StoryError("Bot and ghost names must be different.")
    return StoryParams(place=place, bot_name=bot_name, ghost_name=ghost_name, object_name=object_name)


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
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


CURATED = [
    StoryParams(place="attic", bot_name="Pip", ghost_name="Glim", object_name="a brass lantern"),
    StoryParams(place="hall", bot_name="Milo", ghost_name="Wisp", object_name="a small silver key"),
    StoryParams(place="workshop", bot_name="Ada", ghost_name="Murmur", object_name="a chipped teacup"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show resolved/2."))
        print(sorted((sym.name, tuple(getattr(a, "name", getattr(a, "string", getattr(a, "number", None))) for a in sym.arguments)) for sym in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
