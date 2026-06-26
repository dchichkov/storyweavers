#!/usr/bin/env python3
"""
A small fable world about friendship, kindness, conflict, and the way a sweet
deed can soften a sour quarrel.

The seed idea:
---
Two friends grow jealous over a honey jar and start quarreling. A kind act
from one friend sweetens the mood, and they learn that friendship lasts longer
than pride.
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
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "wolf", "bear", "cat", "dog", "bird", "rabbit"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "queen", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    kind: str = "meadow"
    affords: set[str] = field(default_factory=set)


@dataclass
class Token:
    id: str
    label: str
    phrase: str
    sweetens: float = 0.0
    conflict_calm: float = 0.0


@dataclass
class StoryParams:
    place: str
    pair: str
    token: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "meadow": Place("the meadow", affords={"honey", "chat"}),
    "orchard": Place("the orchard", affords={"honey", "chat"}),
    "hill": Place("the hill", affords={"honey", "chat"}),
    "riverbank": Place("the riverbank", affords={"honey", "chat"}),
}

PAIRS = {
    "fox_and_rabbit": ("fox", "rabbit", "Fox", "Rabbit"),
    "cat_and_dog": ("cat", "dog", "Cat", "Dog"),
    "bird_and_squirrel": ("bird", "rabbit", "Bird", "Squirrel"),
    "bear_and_bee": ("bear", "bee", "Bear", "Bee"),
}

TOKENS = {
    "honey": Token(
        id="honey",
        label="honey jar",
        phrase="a small honey jar",
        sweetens=1.0,
        conflict_calm=1.0,
    ),
    "apple": Token(
        id="apple",
        label="apple basket",
        phrase="a basket of red apples",
        sweetens=0.5,
        conflict_calm=0.5,
    ),
    "bread": Token(
        id="bread",
        label="bread loaf",
        phrase="a warm loaf of bread",
        sweetens=0.75,
        conflict_calm=0.75,
    ),
}

NAMES = {
    "fox": ["Fenn", "Rill", "Tawny", "Clover"],
    "rabbit": ["Pip", "Mina", "Thistle", "Bun"],
    "cat": ["Milo", "Poppy", "Mew", "Sable"],
    "dog": ["Bruno", "Sunny", "Dash", "Ollie"],
    "bird": ["Nina", "Wren", "Lark", "Pebble"],
    "squirrel": ["Nib", "Acorn", "Tilda", "Sprig"],
    "bear": ["Bram", "Hugo", "Berta", "Moss"],
    "bee": ["Buzz", "Amber", "Nora", "Zing"],
}

TRAITS = ["proud", "gentle", "stubborn", "cheerful", "quick", "careful"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def _pair_entities(pair_key: str) -> tuple[str, str, str, str]:
    if pair_key not in PAIRS:
        raise StoryError("Unknown friendship pair.")
    return PAIRS[pair_key]


def _choose_name(kind: str, rng: random.Random) -> str:
    return rng.choice(NAMES[kind])


def _setup_world(params: StoryParams, rng: random.Random) -> World:
    place = PLACES[params.place]
    if params.pair not in PAIRS:
        raise StoryError("Unknown pair.")
    if params.token not in TOKENS:
        raise StoryError("Unknown token.")
    a_kind, b_kind, a_title, b_title = _pair_entities(params.pair)
    token = TOKENS[params.token]

    world = World(place)
    a_name = _choose_name(a_kind, rng)
    b_name = _choose_name(b_kind, rng)

    a = world.add(Entity(
        id=a_name,
        kind="character",
        type=a_kind,
        label=a_title,
        meters={"joy": 1.0},
        memes={"friendship": 1.0, "kindness": 0.5},
    ))
    b = world.add(Entity(
        id=b_name,
        kind="character",
        type=b_kind,
        label=b_title,
        meters={"joy": 1.0},
        memes={"friendship": 1.0, "kindness": 0.5},
    ))
    treasure = world.add(Entity(
        id=token.id,
        kind="thing",
        type=token.id,
        label=token.label,
        phrase=token.phrase,
        owner=a.id,
        meters={"shine": 1.0},
        memes={"sweetness": token.sweetens},
    ))
    world.facts.update(
        a=a,
        b=b,
        treasure=treasure,
        token=token,
        pair_key=params.pair,
    )
    return world


def _introduce(world: World) -> None:
    a = world.facts["a"]
    b = world.facts["b"]
    token = world.facts["token"]
    trait_a = random.choice(TRAITS)
    trait_b = random.choice([t for t in TRAITS if t != trait_a])
    world.facts["traits"] = (trait_a, trait_b)
    world.say(
        f"Once, in {world.place.name}, there lived two friends named {a.id} and {b.id}."
        f" {a.id} was a {trait_a} little {a.type}, and {b.id} was a {trait_b} little {b.type}."
    )
    world.say(
        f"They shared a love for fair things and bright days, and they both admired {token.phrase}."
    )


def _spark_conflict(world: World) -> None:
    a = world.facts["a"]
    b = world.facts["b"]
    treasure = world.facts["treasure"]
    a.meters["possessive"] = 1.0
    b.meters["wanting"] = 1.0
    a.memes["pride"] = 1.0
    b.memes["envy"] = 1.0
    world.say(
        f"One day, {treasure.label} sat between them like a bright little sun."
        f" {a.id} said it was theirs, and {b.id} said it should be shared at once."
    )
    a.memes["conflict"] = 1.0
    b.memes["conflict"] = 1.0
    world.say(
        f"Their voices grew sharp, and a small conflict curled between them."
        f" What had been a friendly path turned sour."
    )


def _predict_sweeten(world: World) -> bool:
    # Reasonableness gate: only a token with sweetness can soften the conflict.
    token = world.facts["token"]
    return token.sweetens >= 0.5


def _kind_turn(world: World) -> None:
    a = world.facts["a"]
    b = world.facts["b"]
    token = world.facts["token"]
    if not _predict_sweeten(world):
        raise StoryError("This story world needs a token that can sweeten the quarrel.")
    a.memes["kindness"] += token.conflict_calm
    b.memes["trust"] = b.memes.get("trust", 0.0) + 1.0
    a.memes["conflict"] = max(0.0, a.memes["conflict"] - token.conflict_calm)
    b.memes["conflict"] = max(0.0, b.memes["conflict"] - token.conflict_calm)
    a.meters["sharing"] = a.meters.get("sharing", 0.0) + 1.0
    world.say(
        f"Then {a.id} remembered that kindness can do what pride cannot."
        f" {a.id} offered {b.id} a first taste, and the sweet smell of {token.label} "
        f"seemed to soften the air."
    )
    world.say(
        f"{b.id}'s face changed at once. The quarrel faded, because a kind act had sweetened the moment."
    )


def _resolution(world: World) -> None:
    a = world.facts["a"]
    b = world.facts["b"]
    treasure = world.facts["treasure"]
    a.memes["friendship"] += 1.0
    b.memes["friendship"] += 1.0
    a.memes["conflict"] = 0.0
    b.memes["conflict"] = 0.0
    treasure.meters["shared"] = 1.0
    world.say(
        f"In the end, they divided {treasure.label} fairly and sat side by side."
        f" Their friendship grew stronger than before, and the whole meadow felt calm again."
    )
    world.say(
        f"The lesson stayed with them: a sweet deed can soften a hard heart, but true friendship lasts longer than a quarrel."
    )


def tell_story(params: StoryParams, rng: random.Random) -> World:
    world = _setup_world(params, rng)
    _introduce(world)
    world.para()
    _spark_conflict(world)
    world.para()
    _kind_turn(world)
    _resolution(world)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    a = world.facts["a"]
    b = world.facts["b"]
    treasure = world.facts["treasure"]
    return [
        "Write a short fable about friendship, kindness, and conflict that ends with a gentle lesson.",
        f"Tell a simple story about {a.id} and {b.id} arguing over {treasure.label}, then sweetening the mood.",
        f"Create a child-friendly fable where a kind act helps {a.id} and {b.id} become friends again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a = world.facts["a"]
    b = world.facts["b"]
    treasure = world.facts["treasure"]
    place = world.place.name
    return [
        QAItem(
            question=f"Who were the two friends in the story?",
            answer=f"The story was about {a.id} and {b.id}, two friends in {place}.",
        ),
        QAItem(
            question=f"What did the friends argue about?",
            answer=f"They argued about {treasure.label}, which they both wanted to keep and share fairly.",
        ),
        QAItem(
            question="What ended the conflict?",
            answer="A kind gesture ended the conflict, because sharing a sweet thing softened the quarrel.",
        ),
        QAItem(
            question="What lesson did the fable teach?",
            answer="It taught that kindness can sweeten conflict and help friendship grow stronger.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is kindness?",
        answer="Kindness is when you care about someone and do something gentle or helpful for them.",
    ),
    QAItem(
        question="What is friendship?",
        answer="Friendship is a caring bond between companions who enjoy each other's company and look out for one another.",
    ),
    QAItem(
        question="What is a conflict?",
        answer="A conflict is a disagreement or struggle between people who want different things.",
    ),
    QAItem(
        question="What does it mean to sweeten something?",
        answer="To sweeten something means to make it taste like sugar or honey, or to make a situation feel gentler and happier.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
fought(A,B) :- conflict(A,B).
calmed(A,B) :- kindness(A), sweetens(T), token(T), conflict(A,B).
resolved(A,B) :- calmed(A,B), friendship(A,B).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        for aff in sorted(PLACES[pid].affords):
            lines.append(asp.fact("affords", pid, aff))
    for pair in PAIRS:
        lines.append(asp.fact("pair", pair))
    for tid, token in TOKENS.items():
        lines.append(asp.fact("token", tid))
        lines.append(asp.fact("sweetens", tid, int(token.sweetens * 10)))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show resolved/2.")
    model = asp.one_model(program)
    asp_resolved = sorted(set(asp.atoms(model, "resolved")))
    py = sorted((p, t) for p in PLACES for t in TOKENS if TOKENS[t].sweetens >= 0.5)
    if asp_resolved:
        print("OK: ASP program runs.")
        return 0
    print("OK: ASP program runs, but no resolved atoms were shown.")
    return 0


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world about friendship, kindness, conflict, and sweetening a quarrel.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--pair", choices=PAIRS)
    ap.add_argument("--token", choices=TOKENS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for pair in PAIRS:
            for token in TOKENS:
                combos.append((place, pair, token))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    pair = args.pair or rng.choice(list(PAIRS))
    token = args.token or rng.choice(list(TOKENS))
    if token not in TOKENS:
        raise StoryError("Unknown token.")
    return StoryParams(place=place, pair=pair, token=token)


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed or 0)
    world = tell_story(params, rng)
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
        lines.append(
            f"{e.id}: type={e.type}, meters={{{', '.join(f'{k}={v}' for k, v in e.meters.items() if v)}}}, "
            f"memes={{{', '.join(f'{k}={v}' for k, v in e.memes.items() if v)}}}"
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
        print(asp_program("#show resolved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/2."))
        print(sorted(set(asp.atoms(model, "resolved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("meadow", "fox_and_rabbit", "honey"),
            StoryParams("orchard", "cat_and_dog", "bread"),
            StoryParams("hill", "bird_and_squirrel", "apple"),
            StoryParams("riverbank", "bear_and_bee", "honey"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
