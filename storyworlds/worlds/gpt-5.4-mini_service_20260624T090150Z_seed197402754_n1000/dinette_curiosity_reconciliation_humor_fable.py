#!/usr/bin/env python3
"""
Story world: Dinette Curiosity Reconciliation Humor Fable.

A tiny fable-like simulation set in a dinette, where curiosity causes a small
mess, humor softens the moment, and reconciliation turns the ending warm.
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
class Place:
    id: str
    label: str
    affordances: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class CuriosityAct:
    id: str
    verb: str
    gerund: str
    peek_verb: str
    topple: str
    concern: str
    consequence: str
    topic: str


@dataclass(frozen=True)
class Treasure:
    id: str
    label: str
    phrase: str
    location: str
    fragile: bool = True
    owner_kind: str = "mouse"


@dataclass(frozen=True)
class Fix:
    id: str
    label: str
    gesture: str
    outcome: str
    covers: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class CharacterSpec:
    name: str
    kind: str
    pronoun_subject: str
    pronoun_object: str
    pronoun_possessive: str
    epithet: str


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def add_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


@dataclass
class StoryParams:
    place: str
    act: str
    treasure: str
    hero: str
    helper: str
    seed: Optional[int] = None


PLACES = {
    "dinette": Place(
        id="dinette",
        label="the little dinette",
        affordances={"peek", "sip", "share", "serve"},
    )
}

ACTIONS = {
    "curiosity": CuriosityAct(
        id="curiosity",
        verb="wonder about the covered plate",
        gerund="wondering about the covered plate",
        peek_verb="lift the lid to peek",
        topple="bumped the sugar jar",
        concern="asked careful questions",
        consequence="made everyone laugh",
        topic="curiosity",
    ),
    "peeking": CuriosityAct(
        id="peeking",
        verb="peek at the shiny tray",
        gerund="peeking at the shiny tray",
        peek_verb="lean close to peek",
        topple="nudged a spoon",
        concern="could not keep still",
        consequence="turned into a silly moment",
        topic="peek",
    ),
}

TREASURES = {
    "pie": Treasure(
        id="pie",
        label="apple pie",
        phrase="a warm apple pie with a crimped crust",
        location="on the counter",
        fragile=True,
        owner_kind="mouse",
    ),
    "jam": Treasure(
        id="jam",
        label="jam tart",
        phrase="a bright jam tart with glossy berries",
        location="on a side tray",
        fragile=True,
        owner_kind="rabbit",
    ),
    "soup": Treasure(
        id="soup",
        label="soup bowl",
        phrase="a steaming bowl of carrot soup",
        location="near the napkins",
        fragile=True,
        owner_kind="mouse",
    ),
}

FIXES = {
    "share": Fix(
        id="share",
        label="a shared spoon",
        gesture="shared the spoon and let everyone have a taste",
        outcome="turned the worry into a treat",
        covers={"peek", "serve"},
    ),
    "apology": Fix(
        id="apology",
        label="a sorry note",
        gesture="said sorry and wiped the sugar together",
        outcome="smoothed the air between them",
        covers={"peek", "serve"},
    ),
    "tea": Fix(
        id="tea",
        label="a little tea break",
        gesture="poured tea for everyone and sat down calmly",
        outcome="made the room feel peaceful again",
        covers={"peek", "sip", "share"},
    ),
}

CHARACTERS = {
    "mouse": CharacterSpec("Milo", "mouse", "he", "him", "his", "small"),
    "rabbit": CharacterSpec("Bina", "rabbit", "she", "her", "her", "bright"),
    "hedgehog": CharacterSpec("Nell", "hedgehog", "she", "her", "her", "quick"),
    "fox": CharacterSpec("Tavi", "fox", "he", "him", "his", "clever"),
}

NAMES = ["Milo", "Bina", "Nell", "Tavi", "Pip", "Luna", "Ollie", "Wren"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(dinette).
affords(dinette,peek).
affords(dinette,sip).
affords(dinette,share).
affords(dinette,serve).

act(curiosity).
act(peeking).

treasure(pie).
treasure(jam).
treasure(soup).

fix(share).
fix(apology).
fix(tea).

compatible(A,T,F) :- act(A), treasure(T), fix(F),
                     needs(A,T),
                     helps(F,A),
                     not blocked(A,T,F).

needs(curiosity,pie).
needs(curiosity,jam).
needs(curiosity,soup).
needs(peeking,pie).
needs(peeking,jam).
needs(peeking,soup).

helps(share,curiosity).
helps(share,peeking).
helps(apology,curiosity).
helps(apology,peeking).
helps(tea,curiosity).
helps(tea,peeking).

blocked(_,_,_) :- false.
#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        for a in sorted(PLACES[pid].affordances):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIONS:
        lines.append(asp.fact("act", aid))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_compatible() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def valid_combo(act: CuriosityAct, treasure: Treasure, place: Place) -> bool:
    return "peek" in place.affordances and treasure.fragile


def valid_pairs() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in PLACES.values():
        for act in ACTIONS.values():
            for treasure in TREASURES.values():
                if valid_combo(act, treasure, place):
                    combos.append((place.id, act.id, treasure.id))
    return combos


def _choose_hero(rng: random.Random, preferred: Optional[str] = None) -> CharacterSpec:
    if preferred and preferred in CHARACTERS:
        return CHARACTERS[preferred]
    return rng.choice(list(CHARACTERS.values()))


def _choose_helper(rng: random.Random, hero: CharacterSpec) -> CharacterSpec:
    options = [c for c in CHARACTERS.values() if c.name != hero.name]
    return rng.choice(options)


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    act = ACTIONS[params.act]
    treasure = TREASURES[params.treasure]
    hero = CHARACTERS[params.hero]
    helper = CHARACTERS[params.helper]

    world = World(place)
    h = world.add(Entity(id="hero", kind="character", label=hero.name))
    s = world.add(Entity(id="helper", kind="character", label=helper.name))
    t = world.add(Entity(id="treasure", kind="thing", label=treasure.label, phrase=treasure.phrase, owner=hero.name, location=treasure.location))

    # Act 1
    world.say(f"At {place.label}, {hero.name} was a {hero.epithet} little {hero.kind} who loved asking questions.")
    world.say(f"{hero.pronoun_subject.capitalize()} was full of {act.topic}, and {hero.pronoun_subject} kept {act.gerund} while {helper.name} watched with a grin.")
    world.say(f"On the counter sat {treasure.phrase}, and {hero.name} could not stop looking at it.")

    # Act 2
    world.para()
    world.say(f"At last, {hero.name} said {hero.pronoun_possessive} big thought out loud: '{act.peek_verb.title()}!'")
    h.add_meme("curiosity", 1)
    h.add_meter("reach", 1)
    t.add_meter("bothered", 1)
    world.say(f"But {hero.name} {act.topple}, and the dinette gave a tiny clink-clink that made even the chairs seem to smile.")
    world.say(f"That little accident {act.consequence}, because nobody could stay stern at such a funny sound.")

    # Act 3
    world.para()
    fix = FIXES["tea"] if treasure.id == "soup" else FIXES["share"] if act.id == "curiosity" else FIXES["apology"]
    h.add_meme("worry", 1)
    s.add_meme("kindness", 1)
    world.say(f"{helper.name} did not scold. Instead, {helper.name} offered {fix.label} and {fix.gesture}.")
    world.say(f"{hero.name} lowered {hero.pronoun_possessive} eyes and said sorry, and {helper.name} forgave {hero.name} at once.")
    world.say(f"Before long, the dinette felt warm again. {fix.outcome.capitalize()}, and {hero.name} and {helper.name} shared a calm little smile over {treasure.phrase}.")

    world.facts.update(
        place=place,
        act=act,
        treasure=treasure,
        hero=hero,
        helper=helper,
        fix=fix,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: CharacterSpec = f["hero"]
    helper: CharacterSpec = f["helper"]
    act: CuriosityAct = f["act"]
    treasure: Treasure = f["treasure"]
    place: Place = f["place"]
    return [
        f"Write a short fable about {hero.name} at {place.label} where curiosity leads to a silly mistake and a kind ending.",
        f"Tell a gentle story in a dinette where {hero.name} wants to {act.verb}, {helper.name} helps, and {treasure.label} stays part of the lesson.",
        f"Create a child-friendly fable with humor and reconciliation about a curious character and a shared table treat.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: CharacterSpec = f["hero"]
    helper: CharacterSpec = f["helper"]
    act: CuriosityAct = f["act"]
    treasure: Treasure = f["treasure"]
    fix: Fix = f["fix"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Who is the story mainly about at {place.label}?",
            answer=f"The story is mainly about {hero.name}, a curious little {hero.kind} who learns a gentle lesson at {place.label}.",
        ),
        QAItem(
            question=f"What did {hero.name} want to do with {treasure.label}?",
            answer=f"{hero.name} wanted to {act.peek_verb.lower()}, because curiosity pulled {hero.pronoun_object} closer and closer to {treasure.phrase}.",
        ),
        QAItem(
            question=f"What happened after {hero.name} made the small mistake?",
            answer=f"The tiny clink made everyone laugh, and then {helper.name} offered {fix.label} so they could reconcile kindly.",
        ),
        QAItem(
            question=f"How did {hero.name} and {helper.name} end the story?",
            answer=f"They ended the story smiling together, because {helper.name} forgave {hero.name} and {fix.outcome}.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "curiosity": [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn about things they do not yet understand.",
        )
    ],
    "reconciliation": [
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making up after a problem so people can be kind to each other again.",
        )
    ],
    "humor": [
        QAItem(
            question="What is humor?",
            answer="Humor is what makes something funny and helps people smile or laugh a little.",
        )
    ],
    "dinette": [
        QAItem(
            question="What is a dinette?",
            answer="A dinette is a small, cozy place for sitting, eating, and talking together.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out: list[QAItem] = []
    for key in ("curiosity", "reconciliation", "humor", "dinette"):
        out.extend(WORLD_KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story Q&A ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    bits = ["--- world trace ---"]
    for e in world.entities.values():
        bits.append(f"{e.id}: kind={e.kind} label={e.label!r} meters={e.meters} memes={e.memes}")
    bits.append(f"fired={sorted(world.fired)}")
    return "\n".join(bits)


# ---------------------------------------------------------------------------
# Story generation and CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="dinette", act="curiosity", treasure="pie", hero="mouse", helper="rabbit"),
    StoryParams(place="dinette", act="peeking", treasure="jam", hero="hedgehog", helper="fox"),
    StoryParams(place="dinette", act="curiosity", treasure="soup", hero="rabbit", helper="mouse"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Dinette fable about curiosity, humor, and reconciliation.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--activity", dest="act", choices=sorted(ACTIONS))
    ap.add_argument("--treasure", choices=sorted(TREASURES))
    ap.add_argument("--hero", choices=sorted(CHARACTERS))
    ap.add_argument("--helper", choices=sorted(CHARACTERS))
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
    place = args.place or "dinette"
    act = args.act or rng.choice(list(ACTIONS))
    treasure = args.treasure or rng.choice(list(TREASURES))
    hero = args.hero or rng.choice(list(CHARACTERS))
    helper = args.helper or rng.choice([k for k in CHARACTERS if k != hero])
    if place not in PLACES:
        raise StoryError("Unknown place.")
    if act not in ACTIONS or treasure not in TREASURES:
        raise StoryError("Unknown activity or treasure.")
    return StoryParams(place=place, act=act, treasure=treasure, hero=hero, helper=helper)


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


def asp_verify() -> int:
    py = set(valid_pairs())
    asp_set = set(asp_compatible())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python:")
    print("only in python:", sorted(py - asp_set))
    print("only in asp:", sorted(asp_set - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_compatible()
        print(f"{len(combos)} compatible combos")
        for c in combos:
            print(c)
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(seed)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            params = resolve_params(args, random.Random(seed + i))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
