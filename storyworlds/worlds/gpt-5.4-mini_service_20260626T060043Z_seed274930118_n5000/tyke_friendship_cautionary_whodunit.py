#!/usr/bin/env python3
"""
tyke_friendship_cautionary_whodunit.py
======================================

A tiny whodunit-style storyworld about friendship, caution, and a small mystery.

Premise:
A tyke notices that something friendly has gone missing or moved in a way that
doesn't make sense. The children follow clues, ask careful questions, and learn
that the best friend is not the one who hides facts, but the one who tells the
truth before the worry grows.

The simulation models:
- one child protagonist ("the tyke")
- one close friend
- one small, physical object that can be misplaced
- one cautionary warning that prevents a bigger mistake
- emotional changes around trust, worry, relief, and friendship

The story is kept short and concrete, with a clue trail and a reveal.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

TYKE_NAMES = ["Milo", "Nia", "Toby", "June", "Pip", "Luna", "Ezra", "Mina"]
FRIEND_NAMES = ["Ada", "Ben", "Cleo", "Otis", "Rae", "Noor", "Theo", "Ivy"]
ADULT_NAMES = ["Mum", "Dad", "Gran", "Auntie Jo", "Uncle Sam"]

PLACES = {
    "classroom": "the classroom",
    "garden": "the garden",
    "hall": "the hall",
    "playroom": "the playroom",
    "shed": "the shed",
}

OBJECTS = {
    "red_ball": ("red ball", "a bright red ball", "toy", "round"),
    "blue_hat": ("blue hat", "a soft blue hat", "hat", "soft"),
    "silver_key": ("silver key", "a tiny silver key", "key", "metal"),
    "yellow_map": ("yellow map", "a folded yellow map", "paper", "folded"),
}

CLUES = {
    "mud": "muddy prints",
    "crumbs": "crumbs",
    "thread": "a loose thread",
    "chalk": "chalk dust",
    "leaf": "a green leaf",
}

CAUTIONS = {
    "look_first": "look before you touch",
    "ask_first": "ask before you take",
    "slow_down": "slow down and check the clues",
}

FRIENDSHIP_BEATS = {
    "share": "shared the clue",
    "help": "helped search",
    "honest": "told the truth",
}


# ---------------------------------------------------------------------------
# Shared entity model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    taken: bool = False
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "tyke", "child"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    place: str
    object_id: str
    clue: str
    caution: str
    name: str
    friend_name: str
    adult_name: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def _clue_amount(world: World, clue: str) -> float:
    return world.get(clue).meters.get("noticed", 0.0)


def propagate(world: World) -> None:
    # A very small whodunit rule set: noticing a clue increases suspicion,
    # and honesty lowers worry while raising trust.
    changed = True
    while changed:
        changed = False

        for ent in world.entities.values():
            if ent.kind != "character":
                continue
            if ent.meters.get("worry", 0) >= 1 and ("comforted", ent.id) not in world.fired:
                world.fired.add(("comforted", ent.id))
                ent.meters["worry"] = max(0.0, ent.meters.get("worry", 0) - 1)
                ent.meters["trust"] = ent.meters.get("trust", 0) + 1
                changed = True

            if ent.meters.get("suspicion", 0) >= 1 and ("resolve", ent.id) not in world.fired:
                world.fired.add(("resolve", ent.id))
                ent.meters["calm"] = ent.meters.get("calm", 0) + 1
                changed = True


def build_world(params: StoryParams) -> World:
    world = World()

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="tyke",
        label="the tyke",
        phrase="a small curious tyke",
        location=params.place,
        meters={"worry": 0.0, "trust": 1.0, "curiosity": 1.0},
        memes={"friendship": 1.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type="child",
        label="the friend",
        phrase="a close friend",
        location=params.place,
        meters={"worry": 0.0, "trust": 1.0},
        memes={"friendship": 1.0, "guilt": 0.0},
    ))
    adult = world.add(Entity(
        id=params.adult_name,
        kind="character",
        type="adult",
        label="the grown-up",
        phrase="a careful grown-up",
        location=params.place,
        meters={"worry": 0.0},
    ))

    obj_label, obj_phrase, obj_kind, obj_shape = OBJECTS[params.object_id]
    item = world.add(Entity(
        id=params.object_id,
        kind="thing",
        type=obj_kind,
        label=obj_label,
        phrase=obj_phrase,
        owner=params.friend_name,
        location=params.place,
        taken=False,
        hidden=True,
        meters={"polish": 1.0},
    ))

    clue = world.add(Entity(
        id=params.clue,
        kind="thing",
        type="clue",
        label=params.clue,
        phrase=CLUES[params.clue],
        location=params.place,
        meters={"noticed": 0.0},
    ))

    caution = world.add(Entity(
        id=params.caution,
        kind="thing",
        type="caution",
        label=params.caution,
        phrase=CAUTIONS[params.caution],
        location=params.place,
    ))

    # Act 1: setup
    world.say(
        f"{hero.id} was a small tyke who liked quiet puzzles and close friends."
    )
    world.say(
        f"One afternoon, {hero.id} and {friend.id} were at {params.place} when "
        f"{friend.id} looked worried."
    )
    world.say(
        f"{friend.id} had been looking after {item.phrase}, but now it was nowhere in sight."
    )

    # Act 2: clues and caution
    world.para()
    world.say(
        f"{hero.id} knelt down and noticed {clue.phrase} near the floor."
    )
    clue.meters["noticed"] = 1.0
    hero.meters["curiosity"] = hero.meters.get("curiosity", 0) + 1
    hero.meters["worry"] = hero.meters.get("worry", 0) + 1
    world.say(
        f"{hero.id} remembered the warning to {CAUTIONS[params.caution]}."
    )
    world.say(
        f"So {hero.id} did not rush. Instead, {hero.id} asked {friend.id} where "
        f"{item.label} had been last seen."
    )
    friend.meters["worry"] = friend.meters.get("worry", 0) + 1
    friend.memes["guilt"] = friend.memes.get("guilt", 0) + 1

    # Act 3: reveal
    world.para()
    world.say(
        f"{friend.id} finally whispered the truth: {friend.id} had moved {item.label} "
        f"to keep it safe, but forgot to tell anyone."
    )
    item.hidden = True
    item.location = params.place
    friend.meters["trust"] = friend.meters.get("trust", 0) + 1
    hero.meters["trust"] = hero.meters.get("trust", 0) + 1
    hero.meters["worry"] = max(0.0, hero.meters.get("worry", 0) - 1)
    friend.memes["guilt"] = 0.0
    world.say(
        f"{adult.id} smiled, because no one had stolen anything after all."
    )
    world.say(
        f"Together they found {item.label} tucked behind a safe box, and the tyke "
        f"laughed with relief."
    )
    world.say(
        f"The clue trail made sense at last: the mystery was small, the friends were honest, "
        f"and the missing thing was never far away."
    )

    propagate(world)

    world.facts.update(
        hero=hero,
        friend=friend,
        adult=adult,
        item=item,
        clue=clue,
        caution=caution,
        params=params,
        revealed=True,
        solved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item = f["item"]
    return [
        f'Write a short whodunit story for children about {hero.id}, a tyke, and a missing {item.label}.',
        f"Tell a cautionary friendship mystery where {friend.id} tells the truth after hiding {item.label} for safety.",
        f'Write a gentle detective story that includes a clue, a warning to {CAUTIONS[f["caution"].id]}, and a happy reveal.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item = f["item"]
    clue = f["clue"]
    caution = f["caution"]
    place = f["params"].place
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a small tyke who liked clues and stayed close to {friend.id} at {place}.",
        ),
        QAItem(
            question=f"What was missing or hidden in the mystery?",
            answer=f"The mystery was about {item.phrase}. It turned out to be hidden safely at {place}.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} start solving the mystery?",
            answer=f"{hero.id} noticed {CLUES[clue.id]}. That clue helped the tyke ask careful questions instead of guessing.",
        ),
        QAItem(
            question=f"What caution did {hero.id} remember?",
            answer=f"{hero.id} remembered to {CAUTIONS[caution.id]}. That helped keep the friendship calm while they searched.",
        ),
        QAItem(
            question=f"How did the mystery end?",
            answer=f"{friend.id} told the truth, the friends found {item.label}, and everyone felt relieved because nothing bad had happened.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone figure out what happened.",
        ),
        QAItem(
            question="Why is it good to tell the truth in a friendship?",
            answer="Telling the truth helps friends trust each other and stops a small worry from growing bigger.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful so you do not make a mistake or miss something important.",
        ),
    ]


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny friendship whodunit storyworld with caution and clues."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--object", dest="object_id", choices=sorted(OBJECTS))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--caution", choices=sorted(CAUTIONS))
    ap.add_argument("--name", choices=TYKE_NAMES)
    ap.add_argument("--friend-name", choices=FRIEND_NAMES)
    ap.add_argument("--adult-name", choices=ADULT_NAMES)
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
    place = args.place or rng.choice(list(PLACES))
    object_id = args.object_id or rng.choice(list(OBJECTS))
    clue = args.clue or rng.choice(list(CLUES))
    caution = args.caution or rng.choice(list(CAUTIONS))
    name = args.name or rng.choice(TYKE_NAMES)
    friend_name = args.friend_name or rng.choice(FRIEND_NAMES)
    adult_name = args.adult_name or rng.choice(ADULT_NAMES)

    if name == friend_name:
        raise StoryError("The tyke and the friend must be different characters.")
    return StoryParams(
        place=place,
        object_id=object_id,
        clue=clue,
        caution=caution,
        name=name,
        friend_name=friend_name,
        adult_name=adult_name,
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.taken:
            bits.append("taken=True")
        if e.hidden:
            bits.append("hidden=True")
        if e.meters:
            bits.append(f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}}")
        if e.memes:
            bits.append(f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the tyke, friend, clue, and object exist together.
valid_story(P, O, C, W) :- place(P), object(O), clue(C), caution(W).

% The cautionary beat is only meaningful if the clue and the hidden object differ.
mystery_pair(O, C) :- object(O), clue(C), O != C.

% A cooperative friendship story is the one where the hidden object is found
% after a clue is noticed and the truth is spoken.
solved_story(P, O, C, W) :- valid_story(P, O, C, W), mystery_pair(O, C).
#show solved_story/4.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for w in CAUTIONS:
        lines.append(asp.fact("caution", w))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show solved_story/4."))
    asp_atoms = set(asp.atoms(model, "solved_story"))
    py_atoms = set()
    for p in PLACES:
        for o in OBJECTS:
            for c in CLUES:
                for w in CAUTIONS:
                    if o != c:
                        py_atoms.add((p, o, c, w))
    if asp_atoms == py_atoms:
        print(f"OK: clingo matches Python ({len(py_atoms)} combinations).")
        return 0
    print("MISMATCH between ASP and Python:")
    if asp_atoms - py_atoms:
        print("  only in ASP:", sorted(asp_atoms - py_atoms))
    if py_atoms - asp_atoms:
        print("  only in Python:", sorted(py_atoms - asp_atoms))
    return 1


# ---------------------------------------------------------------------------
# CLI / output
# ---------------------------------------------------------------------------

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
        print(asp_program("#show solved_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show solved_story/4."))
        atoms = sorted(set(asp.atoms(model, "solved_story")))
        print(f"{len(atoms)} solved combinations:")
        for atom in atoms[:50]:
            print(" ", atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("classroom", "red_ball", "mud", "look_first", "Milo", "Ada", "Mum"),
            StoryParams("garden", "blue_hat", "chalk", "ask_first", "Nia", "Ben", "Dad"),
            StoryParams("hall", "silver_key", "thread", "slow_down", "Pip", "Cleo", "Gran"),
            StoryParams("playroom", "yellow_map", "leaf", "look_first", "June", "Ivy", "Auntie Jo"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(200, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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
            header = f"### {p.name}: {p.place} / {p.object_id} / {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
