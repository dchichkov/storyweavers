#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T185554Z_seed424242_n50/scripture_pimento_bustle_misunderstanding_repetition_bedtime_story.py
===============================================================================================

A small simulated story domain: a child, a misunderstanding about a pimento,
a bustle of bedtime, repetition of explanations, and a gentle resolution.
Style: bedtime story.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Entities
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_repeat_understanding(world: World) -> list[str]:
    """When child misunderstands and parent repeats explanation, understanding grows."""
    out = []
    for child in world.characters():
        if child.id != "child":
            continue
        if child.memes["misunderstanding"] < THRESHOLD:
            continue
        parent = world.get("parent")
        if parent.memes["repeated"] >= child.memes["repetitions_heard"]:
            continue
        # Each repetition increases understanding
        child.memes["understanding"] += 0.5
        child.memes["repetitions_heard"] += 1
        sig = ("understood", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"{child.pronoun('possessive').capitalize()} understanding grew a little.")
    return out


def _r_bustle_effect(world: World) -> list[str]:
    """Parent bustling around makes child curious / adds to the busy feel."""
    out = []
    parent = world.get("parent")
    if parent.memes["bustle_count"] < THRESHOLD:
        return []
    if parent.memes["bustle_count"] >= 2 and not world.fired.add(("bustle_narrated",)):
        out.append("The house felt full of gentle hurry.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="repeat_understanding", tag="social", apply=_r_repeat_understanding),
    Rule(name="bustle_effect", tag="physical", apply=_r_bustle_effect),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Bedtime story beats (state-driven)
# ---------------------------------------------------------------------------
def child_admires_book(world: World, child: Entity, book: Entity) -> None:
    world.say(
        f"{child.id} picked up {book.phrase} and held it like treasure."
    )

def parent_reads_from_book(world: World, parent: Entity, book: Entity, pimento: Entity) -> None:
    world.say(
        f"{parent.label_word} opened the book and began to read about a garden "
        f"where many things grew. One of them was a small red fruit called a pimento."
    )

def child_misunderstands(world: World, child: Entity, pimento: Entity) -> None:
    child.memes["misunderstanding"] += 1
    world.say(
        f"{child.id} stared at the picture. '{pimento.label.capitalize()}? That sounds "
        f"like a fun little friend, not a fruit!' "
    )
    world.say(
        f"{child.pronoun('possessive').capitalize()} {world.get('parent').label_word} "
        f"shook {world.get('parent').pronoun('possessive')} head gently."
    )

def parent_explains(p_world: World, parent: Entity, child: Entity, pimento: Entity) -> None:
    parent.memes["repeated"] += 1
    child.memes["repetitions_heard"] += 1
    world.say(
        f"'A pimento is a small red pepper,' said {parent.label_word}. "
        f"'It is not a toy. It is a vegetable that tastes sweet and a bit smoky.'"
    )

def child_asks_again(world: World, child: Entity, parent: Entity, pimento: Entity) -> None:
    child.memes["misunderstanding"] += 1  # persists until taste
    world.say(
        f"'{pimento.label.capitalize()} wants to come play!' {child.id} insisted, "
        f"and {child.pronoun()} tugged at {parent.pronoun('possessive')} sleeve."
    )

def parent_repeats(world: World, parent: Entity, child: Entity, pimento: Entity) -> None:
    parent.memes["repeated"] += 1
    world.say(
        f"'Listen, sweet one,' said {parent.label_word} once more. 'A pimento is a little '
        f"red pepper that people eat. It is not a playmate.'"
    )

def bustle_bedtime(world: World, parent: Entity) -> None:
    parent.memes["bustle_count"] += 1
    if parent.memes["bustle_count"] == 1:
        world.say(
            f"{parent.label_word.capitalize()} bustled around the room, "
            f"fluffing pillows and folding a blanket."
        )
    elif parent.memes["bustle_count"] == 2:
        world.say(
            f"The bustle grew: {parent.label_word} fetched a glass of water and "
            f"pulled the curtains closed."
        )

def resolution_taste(world: World, child: Entity, parent: Entity, pimento: Entity) -> None:
    child.memes["misunderstanding"] = 0.0
    child.memes["understanding"] = 1.0
    world.say(
        f"At last, {parent.label_word} brought a real pimento from the kitchen. "
        f"'{child.id}, would you like to taste it?'"
    )
    world.say(
        f"{child.id} nodded, took a tiny bite, and {child.pronoun('possessive')} "
        f"eyes grew wide. 'It is sweet!' {child.pronoun()} said. "
        f"'A pimento is a pepper, not a person.'"
    )
    world.say(
        f"Both of them laughed. '{pimento.label.capitalize()} is just a little fruit,' "
        f"{parent.label_word} said, and the misunderstanding melted away like a secret."
    )

def ending(world: World, child: Entity, parent: Entity) -> None:
    world.say(
        f"Before sleep, {parent.label_word} tucked {child.id} in. "
        f"'Tomorrow we can read the scripture again,' {parent.pronoun()} whispered. "
        f"'{child.id} smiled and dreamed of gardens full of tiny red peppers."
    )


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "bedroom": {"place": "the bedroom", "indoor": True},
}

BOOKS = {
    "scripture": {
        "label": "scripture book",
        "phrase": "a worn scripture book with golden edges",
        "plural": False,
    },
}

PIMENTO = {
    "pimento": {
        "label": "pimento",
        "phrase": "a small red pimento",
        "plural": False,
    },
}

CHILD_NAMES = ["Sam", "Lena", "Finn", "Ella", "Nico"]
PARENT_TYPES = ["mother", "father"]
TRAITS = ["curious", "gentle", "eager", "patient"]


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    book: str
    pimento: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Generation prompts & QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c = f["child"]
    return [
        f"Write a bedtime story about a {c.type} named {c.id} who misunderstands "
        f"what a pimento is.",
        f"A parent and child read a scripture book together, but the child thinks "
        f"a pimento is a toy.",
        f"Tell a gentle story about repetition and understanding, ending with a "
        f"taste of a real pimento.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c = f["child"]
    p = f["parent"]
    book = f["book"]
    pimento = f["pimento"]
    sub = c.pronoun("subject")
    pos = c.pronoun("possessive")
    pw = p.label_word
    return [
        QAItem(
            question=f"What did {c.id} think a pimento was?",
            answer=f"{c.id} first thought a pimento was a fun little friend, "
                   f"not a fruit, because {sub} had never seen one before."
        ),
        QAItem(
            question=f"How did {pw} help {c.id} understand?",
            answer=f"{pw.capitalize()} repeated the explanation that a pimento "
                   f"is a small red pepper, and then let {c.id} taste a real "
                   f"pimento so {sub} could learn."
        ),
        QAItem(
            question=f"What happened after {c.id} tasted the pimento?",
            answer=f"{c.id} realized it was sweet and not a person. "
                   f"The misunderstanding ended, and they laughed together."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pimento?",
            answer="A pimento is a small red pepper. It is sweet and mild, "
                   "often used in cooking or stuffed into olives."
        ),
        QAItem(
            question="What does 'bustle' mean?",
            answer="Bustle means to move around in a busy, hurried way. "
                   "Someone who bustles is doing many small tasks quickly."
        ),
        QAItem(
            question="Why do parents sometimes repeat things?",
            answer="Parents repeat things to help children learn and understand. "
                   "Repeating is a loving way to teach."
        ),
    ]


# ---------------------------------------------------------------------------
# Tell the story
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(
        id=params.name, kind="character", type=params.name.lower(),
        traits=["little", params.trait],
    ))
    parent = world.add(Entity(
        id="parent", kind="character", type=params.parent, label=params.parent,
    ))
    book = world.add(Entity(
        id="book", type="book",
        label=BOOKS[params.book]["label"],
        phrase=BOOKS[params.book]["phrase"],
        plural=BOOKS[params.book]["plural"],
        owner=parent.id,
    ))
    pimento = world.add(Entity(
        id="pimento", type="food",
        label=PIMENTO[params.pimento]["label"],
        phrase=PIMENTO[params.pimento]["phrase"],
        plural=False,
    ))

    # Act 1
    world.say(f"Once upon a bedtime, {child.id} was nestled under the covers.")
    child_admires_book(world, child, book)

    world.para()
    parent_reads_from_book(world, parent, book, pimentopek)

    world.para()
    child_misunderstands(world, child, pimento)         # first misunderstanding
    parent_explains(world, parent, child, pimento)      # first repetition
    bustle_bedtime(world, parent)

    # Act 2 – repetition and bustle
    world.para()
    child_asks_again(world, child, parent, pimento)     # second misunderstanding
    parent_repeats(world, parent, child, pimento)       # second repetition
    bustle_bedtime(world, parent)

    # Act 3 – resolution
    world.para()
    resolution_taste(world, child, parent, pimento)
    ending(world, child, parent)

    world.facts = {
        "child": child,
        "parent": parent,
        "book": book,
        "pimento": pimento,
        "setting": params.setting,
    }

    propagate(world, narrate=False)  # finalize any rules
    return world


# ---------------------------------------------------------------------------
# ASP (inline)
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Simple parity: only one story structure exists, but we check parameter consistency.
valid_setting(S) :- setting(S).
valid_book(B) :- book(B).
valid_pimento(P) :- pimento(P).
valid_story(S, B, P, Gender, Parent) :-
    valid_setting(S), valid_book(B), valid_pimento(P),
    plausible_gender(Gender, P), plausible_parent(Parent).
plausible_gender(G, _) :- G = "child".
plausible_parent(P) :- P = "mother"; P = "father".
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for b in BOOKS:
        lines.append(asp.fact("book", b))
    for p in PIMENTO:
        lines.append(asp.fact("pimento", p))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    if model:
        print("OK: ASP finds at least one valid story.")
        return 0
    print("FAIL: ASP found no valid stories.")
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story about a pimento misunderstanding, repetition, and bustle.")
    ap.add_argument("--setting", choices=list(SETTINGS), default="bedroom")
    ap.add_argument("--book", choices=list(BOOKS), default="scripture")
    ap.add_argument("--pimento", choices=list(PIMENTO), default="pimento")
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args, rng):
    if args.seed is None:
        seed = rng.randint(0, 2**31)
    else:
        seed = args.seed
    rng = random.Random(seed)
    return StoryParams(
        setting=args.setting or "bedroom",
        book=args.book or "scripture",
        pimento=args.pimento or "pimento",
        name=args.name or rng.choice(CHILD_NAMES),
        parent=args.parent or rng.choice(PARENT_TYPES),
        trait=rng.choice(TRAITS),
    )


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


def emit(sample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        for e in sample.world.entities.values():
            m = {k: v for k, v in e.meters.items() if v}
            me = {k: v for k, v in e.memes.items() if v}
            print(f"  {e.id}: meters={dict(m)}, memes={dict(me)}")
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"Prompt {i}: {p}")
        for q in sample.story_qa:
            print(f"Q: {q.question}\nA: {q.answer}")
        for q in sample.world_qa:
            print(f"WK Q: {q.question}\nWK A: {q.answer}")


def main():
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/5."))
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed else random.randrange(2**31)
    rng = random.Random(base_seed)

    samples = []
    for _ in range(args.n):
        params = resolve_params(args, rng)
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### {sample.params.name} (trait: {sample.params.trait})" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
