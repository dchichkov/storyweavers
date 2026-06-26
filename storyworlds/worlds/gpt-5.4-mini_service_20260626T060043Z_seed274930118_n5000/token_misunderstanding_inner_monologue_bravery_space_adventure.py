#!/usr/bin/env python3
"""
A small standalone storyworld: a space adventure built around a token, a
misunderstanding, inner monologue, and bravery.

Premise:
A young cadet needs a shiny token to enter a star gate and deliver a package.
A misunderstanding makes them think the token is lost or stolen. The cadet
thinks through the problem, gathers courage, and discovers a simple fix.

The world is intentionally small and state-driven:
- characters have meters and memes
- the token is a physical object with ownership and location
- the misunderstanding changes emotional state and blocks progress
- bravery is a resolve meter that lets the cadet speak up and investigate
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "pilot", "captain", "cadet_girl"}
        male = {"boy", "man", "pilot_boy", "captain_boy", "cadet_boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Ship:
    name: str = "the Silver Comet"
    gate: str = "the star gate"
    dock: str = "Dock Seven"
    corridor: str = "the long corridor"
    bay: str = "the arrival bay"


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    token_label: str = "token"
    token_phrase: str = "a bright silver token"
    seed: Optional[int] = None


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SHIP = Ship()

HEROES = [
    ("Nova", "girl"),
    ("Kai", "boy"),
    ("Luna", "girl"),
    ("Milo", "boy"),
    ("Pip", "cadet"),
]

HELPERS = [
    ("Rin", "girl"),
    ("Jax", "boy"),
    ("Bea", "girl"),
    ("Orrin", "boy"),
]

LOCATIONS = {
    "dock": "the dock",
    "corridor": "the long corridor",
    "bay": "the arrival bay",
    "gate": "the star gate",
}

EMOTIONS = ["curious", "worried", "quiet", "brave", "hopeful"]


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def _hero_article(hero: Entity) -> str:
    return "a" if hero.type not in {"girl", "boy"} else "a"


def _setting_line() -> str:
    return (
        f"On {SHIP.name}, {SHIP.dock} glowed with blue lights, and {SHIP.corridor} "
        f"echoed with soft boot steps."
    )


def _inner_monologue(hero: Entity, token: Entity) -> str:
    return (
        f"{hero.pronoun('subject').capitalize()} took a slow breath. "
        f'"If I check carefully, I can find my {token.label}," '
        f"{hero.noun()} told {hero.pronoun('object')}self."
    )


def _misunderstanding_line(hero: Entity, helper: Entity, token: Entity) -> str:
    return (
        f"{helper.noun().capitalize()} pointed at the floor and said, "
        f'"I think the {token.label} rolled away!" '
        f"But {hero.noun()} misunderstood and thought {helper.pronoun('subject')} "
        f"meant someone had taken it."
    )


def _bravery_line(hero: Entity) -> str:
    return (
        f"{hero.pronoun('subject').capitalize()} felt a wobble in {hero.pronoun('possessive')} chest, "
        f"but {hero.noun()} stayed brave and walked back toward the light."
    )


def tell(world: World, params: StoryParams) -> World:
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        location="dock",
        meters={"distance": 0.0},
        memes={"worry": 0.0, "bravery": 0.0, "curiosity": 0.0, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper_type,
        label=params.helper_name,
        location="dock",
        meters={"distance": 0.0},
        memes={"kindness": 0.0},
    ))
    token = world.add(Entity(
        id="token",
        kind="thing",
        type="token",
        label=params.token_label,
        phrase=params.token_phrase,
        owner=hero.id,
        location="pocket",
        carried_by=hero.id,
    ))

    world.say(
        f"{hero.label} was a young space cadet with a small mission: deliver a message "
        f"to {SHIP.gate} before the station lights turned green."
    )
    world.say(
        f"{hero.label} had {token.phrase}, and that little {token.label} could open the gate."
    )
    world.say(
        f"{hero.label} liked the warm hum of engines, but the mission felt extra big "
        f"because everything important on a ship seemed to have one tiny key."
    )

    world.para()
    world.say(_setting_line())
    world.say(
        f"{hero.label} hurried into {SHIP.corridor} with {helper.label} beside {hero.pronoun('object')}."
    )
    hero.meters["distance"] += 1
    helper.meters["distance"] += 1
    hero.memes["curiosity"] += 1

    world.say(_misunderstanding_line(hero, helper, token))
    hero.memes["worry"] += 1
    world.facts["misunderstanding"] = True
    world.facts["token_seen"] = True
    world.facts["token_lost"] = False

    world.para()
    world.say(
        f"{hero.label} looked at the shiny deck panels and felt a little twist of fear."
    )
    world.say(_inner_monologue(hero, token))
    hero.memes["bravery"] += 1
    world.say(_bravery_line(hero))

    world.say(
        f"{hero.label} bent down and looked under a cable crate, then behind a hovering crate, "
        f"and finally under {SHIP.dock}'s bench."
    )
    token.location = "under a cable crate"

    world.say(
        f"There, tucked beside a blinking screwdriver, was the {token.label} all along."
    )
    token.location = hero.id
    token.carried_by = hero.id
    hero.memes["worry"] = 0.0
    hero.memes["relief"] += 1
    helper.memes["kindness"] += 1

    world.para()
    world.say(
        f"{helper.label} gave a sheepish smile. "
        f'"Oh! I meant it rolled away, not that someone stole it," {helper.label} said.'
    )
    world.say(
        f"{hero.label} laughed, tucked the {token.label} safely into {hero.pronoun('possessive')} pocket, "
        f"and marched to {SHIP.gate} with new courage."
    )
    world.say(
        f"This time, the gate opened with a happy chime, and {hero.label} delivered the message on time."
    )

    world.facts.update(hero=hero, helper=helper, token=token, ship=world.ship)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    token: Entity = f["token"]
    return [
        f'Write a short space adventure about {hero.label}, a young cadet, and a missing {token.label}.',
        "Tell a child-friendly story in which a misunderstanding causes worry, but inner monologue and bravery help fix it.",
        f'Write a tiny spaceship story that includes the word "{token.label}" and ends with a gate opening.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    token: Entity = f["token"]
    return [
        QAItem(
            question=f"What was {hero.label}'s mission?",
            answer=f"{hero.label} needed to carry a message to {SHIP.gate} and use the {token.label} to open it.",
        ),
        QAItem(
            question=f"What did {helper.label} say that got misunderstood?",
            answer=f"{helper.label} said the {token.label} had rolled away, but {hero.label} thought someone had taken it.",
        ),
        QAItem(
            question=f"What helped {hero.label} stay calm?",
            answer=f"{hero.label} used an inner monologue, took a breath, and chose bravery instead of panic.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{hero.label} found the {token.label}, laughed with {helper.label}, and the star gate opened with a cheerful chime.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a token in a space station story?",
            answer="A token can be a small special object that proves permission or helps open a locked place.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone hears or thinks the wrong thing, even though nobody meant to cause trouble.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet thinking a character does inside their own head.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is when someone feels scared but still does the right thing.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(K) :- helper_name(K).
token(T) :- token_label(T).
misunderstanding :- said_rolled_away, thought_stolen.
bravery :- worry(hero), breath(hero), search(hero), find(token).
resolved :- misunderstanding, bravery, token_found.
#show misunderstanding/0.
#show bravery/0.
#show resolved/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy
    lines = [
        asp.fact("hero_name", "hero"),
        asp.fact("helper_name", "helper"),
        asp.fact("token_label", "token"),
        asp.fact("said_rolled_away"),
        asp.fact("thought_stolen"),
        asp.fact("worry", "hero"),
        asp.fact("breath", "hero"),
        asp.fact("search", "hero"),
        asp.fact("find", "token"),
        asp.fact("token_found"),
    ]
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp  # lazy
    model = asp.one_model(asp_program())
    shown = {s.name for s in model}
    expected = {"misunderstanding", "bravery", "resolved"}
    if shown == expected:
        print("OK: ASP model matches the Python story gate.")
        return 0
    print(f"MISMATCH: got {sorted(shown)} expected {sorted(expected)}")
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld with a token misunderstanding.")
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy", "cadet"], default=None)
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy"], default=None)
    ap.add_argument("--token-label", default="token")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero_name, hero_type = rng.choice(HEROES)
    helper_name, helper_type = rng.choice(HELPERS)

    if args.name:
        hero_name = args.name
    if args.hero_type:
        hero_type = args.hero_type
    if args.helper_name:
        helper_name = args.helper_name
    if args.helper_type:
        helper_type = args.helper_type

    if args.token_label.strip().lower() != "token":
        raise StoryError("This storyworld is built around a token; please keep --token-label token.")

    return StoryParams(
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        token_label="token",
        token_phrase="a bright silver token",
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SHIP)
    tell(world, params)
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if ent.kind == "thing":
            bits.append(f"location={ent.location}")
            if ent.carried_by:
                bits.append(f"carried_by={ent.carried_by}")
        lines.append(f"{ent.id}: {' '.join(bits)}")
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp  # lazy
        model = asp.one_model(asp_program())
        print("ASP shown atoms:", [str(a) for a in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Nova", "girl", "Rin", "girl"),
            StoryParams("Kai", "boy", "Jax", "boy"),
            StoryParams("Luna", "girl", "Bea", "girl"),
            StoryParams("Milo", "boy", "Orrin", "boy"),
        ]
        for p in curated:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 25):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
