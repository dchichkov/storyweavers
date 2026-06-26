#!/usr/bin/env python3
"""
A small pirate-tale storyworld set in a friend's backyard.

Seed tale:
A little pirate-pretend kid visits a friend's backyard with a prized commodity
(trinkets for trading). A peeve about sharing makes the play tense, but a foreshadowed
glimmer leads to a surprise discovery and a lesson learned about fair trades.
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
# Domain registries
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Commodity:
    id: str
    label: str
    phrase: str
    trade_value: int
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Peeve:
    id: str
    label: str
    phrase: str
    trigger: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Surprise:
    id: str
    label: str
    phrase: str
    discovered_by: str
    reward: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Lesson:
    id: str
    lesson_learned: str
    phrase: str
    tags: set[str] = field(default_factory=set)


COMMODITIES = {
    "shells": Commodity(
        id="shells",
        label="shells",
        phrase="a pouch of shiny shells",
        trade_value=2,
        tags={"sea", "trade", "shiny"},
    ),
    "buttons": Commodity(
        id="buttons",
        label="buttons",
        phrase="a handful of brass buttons",
        trade_value=1,
        tags={"trade", "small", "shiny"},
    ),
    "coins": Commodity(
        id="coins",
        label="coins",
        phrase="three round copper coins",
        trade_value=3,
        tags={"trade", "metal", "shiny"},
    ),
}

PEEVES = {
    "hogging": Peeve(
        id="hogging",
        label="hogging",
        phrase="the peeve of hogging all the best toys",
        trigger="would not share",
        tags={"share", "fair", "annoyed"},
    ),
    "interrupting": Peeve(
        id="interrupting",
        label="interrupting",
        phrase="the peeve of interrupting every turn",
        trigger="kept cutting in",
        tags={"talk", "fair", "annoyed"},
    ),
    "grabbing": Peeve(
        id="grabbing",
        label="grabbing",
        phrase="the peeve of grabbing first",
        trigger="snatched before asking",
        tags={"share", "hands", "annoyed"},
    ),
}

SURPRISES = {
    "treasure": Surprise(
        id="treasure",
        label="buried treasure",
        phrase="a small chest buried under a watering can",
        discovered_by="a muddy glint",
        reward="a fair trade for both friends",
        tags={"treasure", "surprise", "gold"},
    ),
    "map": Surprise(
        id="map",
        label="a map",
        phrase="a folded map tucked under the porch step",
        discovered_by="a scrap of blue paper",
        reward="a clue to the hidden prize",
        tags={"map", "surprise", "clue"},
    ),
    "bottle": Surprise(
        id="bottle",
        label="a message bottle",
        phrase="a bottle with a rolled note inside",
        discovered_by="a glass sparkle in the grass",
        reward="a silly pirate riddle",
        tags={"message", "surprise", "riddle"},
    ),
}

LESSONS = {
    "share": Lesson(
        id="share",
        lesson_learned="sharing makes the game bigger for everyone",
        phrase="a lesson about sharing",
        tags={"share", "fair"},
    ),
    "ask": Lesson(
        id="ask",
        lesson_learned="asking first is kinder than taking first",
        phrase="a lesson about asking before taking",
        tags={"share", "ask", "fair"},
    ),
    "listen": Lesson(
        id="listen",
        lesson_learned="listening helps a crew solve trouble faster",
        phrase="a lesson about listening",
        tags={"talk", "listen", "fair"},
    ),
}

FRIENDS = ["Mia", "Noah", "Lily", "Ben", "Ava", "Theo", "Zoe", "Max"]
NICKNAMES = ["Captain", "First Mate", "Little Swashbuckler", "Deckhand", "Matey"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)


@dataclass
class StoryParams:
    friend_name: str
    hero_name: str
    commodity: str
    peeve: str
    surprise: str
    lesson: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "label": v.label, "type": v.type,
            "owner": v.owner, "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Reasonable story gate
# ---------------------------------------------------------------------------

def valid_story(commodity: Commodity, peeve: Peeve, surprise: Surprise, lesson: Lesson) -> bool:
    return (
        commodity.trade_value >= 1
        and "annoyed" in peeve.tags
        and "surprise" in surprise.tags
        and "fair" in lesson.tags
    )


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------

def intro_line(hero: str, friend: str, commodity: Commodity) -> str:
    return (
        f"{hero} came to {friend}'s backyard like a tiny pirate with a steady grin, "
        f"carrying {commodity.phrase} as if it were the richest cargo on the sea."
    )


def foreshadow_line(surprise: Surprise) -> str:
    return (
        f"Near the flower bed, {surprise.discovered_by} flashed once and vanished, "
        f"like the yard itself was keeping a secret."
    )


def conflict_line(hero: str, friend: str, peeve: Peeve, commodity: Commodity) -> str:
    return (
        f"At first, {friend} got {peeve.label} because {friend} {peeve.trigger}, "
        f"and {hero} tightened a small fist around the {commodity.label}."
    )


def turn_line(hero: str, friend: str, surprise: Surprise) -> str:
    return (
        f"Then the strange glint returned beside the watering can, and both kids "
        f"leaned in together to see what {surprise.phrase} really was."
    )


def resolution_line(hero: str, friend: str, lesson: Lesson, surprise: Surprise) -> str:
    return (
        f"After that, {hero} and {friend} split the find fairly and learned that "
        f"{lesson.lesson_learned}. The surprise turned into {surprise.reward}."
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_story(params: StoryParams) -> StorySample:
    world = World()
    commodity = COMMODITIES[params.commodity]
    peeve = PEEVES[params.peeve]
    surprise = SURPRISES[params.surprise]
    lesson = LESSONS[params.lesson]

    hero = world.add(Entity(id=params.hero_name, kind="character", type="pirate-kid", label=params.hero_name))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="friend", label=params.friend_name))
    cargo = world.add(Entity(id="commodity", kind="thing", type=commodity.id, label=commodity.label, owner=hero.id))
    world.add(Entity(id="peeve", kind="thing", type=peeve.id, label=peeve.label))
    world.add(Entity(id="surprise", kind="thing", type=surprise.id, label=surprise.label))
    world.add(Entity(id="lesson", kind="thing", type=lesson.id, label=lesson.phrase))

    hero.memes["hope"] = 1
    friend.memes["mood"] = 0
    world.facts.update(
        hero=hero.id,
        friend=friend.id,
        commodity=commodity,
        peeve=peeve,
        surprise=surprise,
        lesson=lesson,
    )

    world.say(intro_line(hero.id, friend.id, commodity))
    world.say(
        f"{hero.id} had a little plan to trade the {commodity.label} for a game, "
        f"but a cranky breeze of {peeve.phrase} spoiled the first turn."
    )
    world.say(foreshadow_line(surprise))
    world.para()

    friend.memes["annoyance"] = 1
    hero.memes["peeve"] = 1
    world.say(conflict_line(hero.id, friend.id, peeve, commodity))
    world.say(
        f"{hero.id} almost walked off in a huff, but the glitter in the dirt kept "
        f"pulling both of them back."
    )
    world.say(turn_line(hero.id, friend.id, surprise))
    world.para()

    hero.memes["surprise"] = 1
    friend.memes["surprise"] = 1
    world.say(
        f"It was not treasure for one kid alone; it was a clue wrapped in mud, "
        f"so they had to work side by side."
    )
    world.say(resolution_line(hero.id, friend.id, lesson, surprise))
    world.say(
        f"In the end, the backyard felt bigger than before, and {cargo.label} "
        f"was still safe in {hero.id}'s palm while both friends laughed like pirates."
    )

    prompts = [
        f'Write a Pirate Tale set in a friend\'s backyard that includes "{commodity.label}" and a peeve.',
        f"Tell a short story where {params.hero_name} and {params.friend_name} argue, find a surprise, and learn a lesson.",
        f"Write a gentle backyard pirate story with foreshadowing, surprise, and a lesson learned.",
    ]

    story_qa = [
        QAItem(
            question=f"What did {params.hero_name} bring to {params.friend_name}'s backyard?",
            answer=f"{params.hero_name} brought {commodity.phrase} to trade like pirate treasure.",
        ),
        QAItem(
            question=f"What peeve made the first part of the story tense?",
            answer=f"The peeve was {peeve.phrase}, which made {params.friend_name} act annoyed.",
        ),
        QAItem(
            question=f"What surprise did the kids discover together?",
            answer=f"They discovered {surprise.phrase}.",
        ),
        QAItem(
            question=f"What lesson did the kids learn by the end?",
            answer=f"They learned that {lesson.lesson_learned}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a commodity?",
            answer="A commodity is something useful or valuable that people can trade, like shells, coins, or buttons.",
        ),
        QAItem(
            question="What is a peeve?",
            answer="A peeve is a little annoyance that can make someone grumpy or impatient.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a small clue that hints something important may happen later.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something unexpected that changes what the characters thought would happen.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
commodity(C) :- commodity_name(C).
peeve(P) :- peeve_name(P).
surprise(S) :- surprise_name(S).
lesson(L) :- lesson_name(L).

valid_story(C,P,S,L) :- commodity(C), peeve(P), surprise(S), lesson(L),
                        commodity_value(C,V), V >= 1,
                        peeve_annoying(P),
                        surprise_clue(S),
                        lesson_fair(L).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, c in COMMODITIES.items():
        lines.append(asp.fact("commodity_name", cid))
        lines.append(asp.fact("commodity_value", cid, c.trade_value))
    for pid, p in PEEVES.items():
        lines.append(asp.fact("peeve_name", pid))
        lines.append(asp.fact("peeve_annoying", pid))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise_name", sid))
        lines.append(asp.fact("surprise_clue", sid))
    for lid, l in LESSONS.items():
        lines.append(asp.fact("lesson_name", lid))
        lines.append(asp.fact("lesson_fair", lid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple[str, str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {
        (c.id, p.id, s.id, l.id)
        for c in COMMODITIES.values()
        for p in PEEVES.values()
        for s in SURPRISES.values()
        for l in LESSONS.values()
        if valid_story(c, p, s, l)
    }
    try:
        asp_set = set(asp_valid_stories())
    except Exception as exc:
        print(f"ASP unavailable or failed: {exc}")
        return 1
    if py == asp_set:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    if py - asp_set:
        print("Only in Python:", sorted(py - asp_set))
    if asp_set - py:
        print("Only in ASP:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale backyard storyworld with commodity, peeve, surprise, and lesson learned.")
    ap.add_argument("--commodity", choices=sorted(COMMODITIES))
    ap.add_argument("--peeve", choices=sorted(PEEVES))
    ap.add_argument("--surprise", choices=sorted(SURPRISES))
    ap.add_argument("--lesson", choices=sorted(LESSONS))
    ap.add_argument("--hero", choices=FRIENDS)
    ap.add_argument("--friend", choices=FRIENDS)
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
    commodity = args.commodity or rng.choice(sorted(COMMODITIES))
    peeve = args.peeve or rng.choice(sorted(PEEVES))
    surprise = args.surprise or rng.choice(sorted(SURPRISES))
    lesson = args.lesson or rng.choice(sorted(LESSONS))
    if not valid_story(COMMODITIES[commodity], PEEVES[peeve], SURPRISES[surprise], LESSONS[lesson]):
        raise StoryError("No valid story matches those choices.")
    hero = args.hero or rng.choice(FRIENDS)
    friend = args.friend or rng.choice([n for n in FRIENDS if n != hero])
    return StoryParams(
        hero_name=hero,
        friend_name=friend,
        commodity=commodity,
        peeve=peeve,
        surprise=surprise,
        lesson=lesson,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        bits = []
        if ent.owner:
            bits.append(f"owner={ent.owner}")
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        lines.append(f"{ent.id}: {ent.kind} {ent.label} {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== story qa ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world qa ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


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
    StoryParams(hero_name="Mia", friend_name="Ben", commodity="shells", peeve="hogging", surprise="treasure", lesson="share"),
    StoryParams(hero_name="Noah", friend_name="Ava", commodity="coins", peeve="interrupting", surprise="map", lesson="listen"),
    StoryParams(hero_name="Zoe", friend_name="Theo", commodity="buttons", peeve="grabbing", surprise="bottle", lesson="ask"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        for row in asp_valid_stories():
            print(" ".join(row))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            i += 1
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} and {p.friend_name} | commodity={p.commodity} peeve={p.peeve}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
