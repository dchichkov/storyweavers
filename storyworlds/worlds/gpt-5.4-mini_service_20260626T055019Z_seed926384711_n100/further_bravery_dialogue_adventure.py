#!/usr/bin/env python3
"""
storyworlds/worlds/further_bravery_dialogue_adventure.py
=========================================================

A small adventure storyworld about going further than expected, speaking up,
and finding bravery by talking through a problem.

This world models:
- a seeker who wants to go further on a path
- a companion who worries about danger
- a real physical risk in meters: distance into a place, a token to retrieve
- emotional memes: worry, courage, trust, relief

The story always has a clear arc:
setup -> warning -> brave dialogue -> safe action -> return with a change.
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

# -----------------------------
# World model
# -----------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carrier: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    kind: str
    has: set[str] = field(default_factory=set)
    farther_name: str = ""
    safe_turnback: str = ""


@dataclass
class Token:
    id: str
    label: str
    phrase: str
    found_in: str
    return_word: str
    value: str


@dataclass
class StoryParams:
    place: str
    token: str
    hero_name: str
    hero_type: str
    companion_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[list[str]] = [[]]
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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.lines = [[]]
        w.fired = set(self.fired)
        return w


# -----------------------------
# Registries
# -----------------------------
PLACES = {
    "wood": Place(
        id="wood",
        label="the wood path",
        kind="wild",
        has={"trail", "bridge"},
        farther_name="the deeper trees",
        safe_turnback="the bright path home",
    ),
    "cave": Place(
        id="cave",
        label="the cave mouth",
        kind="wild",
        has={"stones", "narrow_passage"},
        farther_name="the farther tunnel",
        safe_turnback="the sunlit mouth",
    ),
    "river": Place(
        id="river",
        label="the riverbank",
        kind="wild",
        has={"bank", "log"},
        farther_name="the bend beyond the reeds",
        safe_turnback="the dry bank",
    ),
}

TOKENS = {
    "lantern": Token(
        id="lantern",
        label="lantern",
        phrase="a little brass lantern",
        found_in="cave",
        return_word="light",
        value="glow",
    ),
    "map": Token(
        id="map",
        label="map",
        phrase="a folded trail map",
        found_in="wood",
        return_word="find their way",
        value="direction",
    ),
    "shell": Token(
        id="shell",
        label="shell",
        phrase="a pale shell with a spiral line",
        found_in="river",
        return_word="hold on to the memory",
        value="memory",
    ),
}

HERO_NAMES = ["Maya", "Leo", "Nina", "Owen", "Ivy", "Theo", "Luna", "Eli"]
TRAITS = ["curious", "spirited", "careful", "restless", "gentle", "brave"]


# -----------------------------
# Story logic
# -----------------------------
def challenge_risk(place: Place, token: Token) -> bool:
    return place.id == token.found_in


def reasonableness_gate(place: Place, token: Token) -> bool:
    return challenge_risk(place, token)


def think_further(world: World, hero: Entity, companion: Entity, token: Token) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    companion.memes["worry"] = companion.memes.get("worry", 0) + 1
    world.say(
        f"{hero.id} loved looking further down the path, because every bend felt like a new secret."
    )
    world.say(
        f"{hero.pronoun().capitalize()} and {companion.label} had come to {world.place.label}, "
        f"where the air felt different and the {token.label} might be waiting."
    )


def warn_about_distance(world: World, companion: Entity, hero: Entity, token: Token) -> None:
    companion.memes["worry"] = companion.memes.get("worry", 0) + 1
    world.say(
        f'"We should not go too far," {companion.pronoun()} said. '
        f'"If we lose the {token.label}, we may not find our way back."'
    )


def brave_reply(world: World, hero: Entity, companion: Entity, token: Token) -> None:
    hero.memes["courage"] = hero.memes.get("courage", 0) + 1
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    world.say(
        f'{hero.id} took a slow breath. "I am scared too," {hero.pronoun()} said, '
        f'"but we can talk about it and go one small step at a time."'
    )


def agree_to_plan(world: World, companion: Entity, hero: Entity, token: Token) -> None:
    companion.memes["worry"] = max(0.0, companion.memes.get("worry", 0) - 1)
    companion.memes["trust"] = companion.memes.get("trust", 0) + 1
    world.say(
        f'{companion.label} nodded. "All right," {companion.pronoun()} said. '
        f'"We will keep the path in sight and stop if the dark feels too close."'
    )


def reach_and_return(world: World, hero: Entity, companion: Entity, token: Token) -> None:
    hero.meters["distance"] = hero.meters.get("distance", 0) + 1
    world.say(
        f"They went a little further, just enough to reach {token.phrase}."
    )
    world.say(
        f'{hero.id} picked up the {token.label} and grinned. It was not just a thing to carry; '
        f'it was proof that brave talk can turn a scary choice into a safe one.'
    )
    world.say(
        f'Then they followed the {world.place.safe_turnback}, and the road home felt easier than before.'
    )
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    companion.memes["relief"] = companion.memes.get("relief", 0) + 1


def tell(place: Place, token: Token, hero_name: str, hero_type: str, companion_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    companion = world.add(Entity(id="Companion", kind="character", type=companion_type, label="the companion"))
    treasure = world.add(Entity(id=token.id, type="thing", label=token.label, phrase=token.phrase, owner=hero.id))
    world.facts.update(hero=hero, companion=companion, token=treasure, place=place, trait=trait)

    world.say(
        f"{hero.id} was a {trait} {hero.type} who wanted to go further than the last marker on the path."
    )
    world.say(
        f"{hero.id} had heard a small story about {token.phrase}, and {hero.pronoun()} wanted to bring it home."
    )

    world.para()
    think_further(world, hero, companion, treasure)
    warn_about_distance(world, companion, hero, treasure)
    brave_reply(world, hero, companion, treasure)
    agree_to_plan(world, companion, hero, treasure)

    world.para()
    reach_and_return(world, hero, companion, treasure)
    return world


# -----------------------------
# Q&A
# -----------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    companion: Entity = f["companion"]  # type: ignore[assignment]
    token: Entity = f["token"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    return [
        f'Write a short adventure story for a young child about bravery and dialogue at {place.label}.',
        f"Tell a gentle tale where {hero.id} wants to go further, {companion.label} worries, and they use kind dialogue to solve it.",
        f'Create a simple story that includes the word "further" and ends with a safe return from {place.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    companion: Entity = f["companion"]  # type: ignore[assignment]
    token: Entity = f["token"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    trait: str = f["trait"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {place.label}?",
            answer=f"{hero.id} wanted to go further down the path and bring home the {token.label}.",
        ),
        QAItem(
            question=f"Why did {companion.label} worry?",
            answer=f"{companion.label} worried that going too far might make them lose the way back, so the two needed a careful plan.",
        ),
        QAItem(
            question=f"How did {trait} {hero.id} and {companion.label} solve the problem?",
            answer=f"They talked about the fear, took one small step at a time, and agreed to stay close to the safe turnback.",
        ),
        QAItem(
            question=f"What did {hero.id} carry home in the end?",
            answer=f"{hero.id} carried home {token.phrase}, and it felt like proof that brave words can help with a hard choice.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "further": [
        QAItem(
            question="What does it mean to go further?",
            answer="To go further means to travel more ahead, or to move farther away from where you started.",
        )
    ],
    "bravery": [
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing what is needed even when you feel scared.",
        )
    ],
    "dialogue": [
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is a conversation between people, where they talk and listen to each other.",
        )
    ],
    "adventure": [
        QAItem(
            question="What is an adventure?",
            answer="An adventure is an exciting trip or event that may include surprises, challenges, and discovery.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        item
        for key in ["further", "bravery", "dialogue", "adventure"]
        for item in WORLD_KNOWLEDGE[key]
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


# -----------------------------
# ASP twin
# -----------------------------
ASP_RULES = r"""
place(P) :- setting(P).
token(T) :- treasure(T).
risk(P,T) :- place(P), token(T), found_in(T,P).
reasonable(P,T) :- risk(P,T).
#show reasonable/2.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES.values():
        lines.append(asp.fact("setting", p.id))
    for t in TOKENS.values():
        lines.append(asp.fact("treasure", t.id))
        lines.append(asp.fact("found_in", t.id, t.found_in))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/2."))
    return sorted(set(asp.atoms(model, "reasonable")))


def python_valid_pairs() -> list[tuple]:
    return sorted((p.id, t.id) for p in PLACES.values() for t in TOKENS.values() if reasonableness_gate(p, t))


def asp_verify() -> int:
    py = set(python_valid_pairs())
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(py)} pairs).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# -----------------------------
# Params and generation
# -----------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld about further bravery and dialogue.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--token", choices=sorted(TOKENS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    valid = [(p.id, t.id) for p in PLACES.values() for t in TOKENS.values() if reasonableness_gate(p, t)]
    combos = [
        c for c in valid
        if (args.place is None or c[0] == args.place)
        and (args.token is None or c[1] == args.token)
    ]
    if not combos:
        raise StoryError("(No valid adventure matches the given options.)")
    place_id, token_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    companion = args.companion or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place_id, token=token_id, hero_name=name, hero_type=gender, companion_type=companion, trait=trait)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    token = TOKENS[params.token]
    world = tell(place, token, params.hero_name, params.hero_type, params.companion_type, params.trait)
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
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
    StoryParams(place="wood", token="map", hero_name="Maya", hero_type="girl", companion_type="mother", trait="curious"),
    StoryParams(place="cave", token="lantern", hero_name="Leo", hero_type="boy", companion_type="father", trait="brave"),
    StoryParams(place="river", token="shell", hero_name="Ivy", hero_type="girl", companion_type="mother", trait="spirited"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} reasonable place-token pairs:\n")
        for p, t in pairs:
            print(f"  {p:8} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
