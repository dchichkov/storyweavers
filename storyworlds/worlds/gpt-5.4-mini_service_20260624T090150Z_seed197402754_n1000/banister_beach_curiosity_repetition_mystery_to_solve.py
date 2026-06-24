#!/usr/bin/env python3
"""
A small bedtime-story world set at the beach, with curiosity, repetition, and a
little mystery to solve. A child keeps noticing a strange banister by the sand,
returns to it again and again, and learns what it is for.
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

BEACHES = {
    "beach": {
        "name": "the beach",
        "detail": "the warm beach",
    }
}

MYSTERIES = {
    "rope": "a loop of rope",
    "shell": "a shiny shell",
    "note": "a folded note",
    "star": "a little starfish charm",
}

REPETITIONS = {
    "counting": "count the steps",
    "returning": "walk back to the banister",
    "peeking": "peek through the rails",
}

NAMES = ["Mia", "Lina", "Nora", "Theo", "Ben", "Ivy", "Ava", "Leo"]
TRAITS = ["curious", "gentle", "sleepy", "thoughtful", "quiet"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    trait: str
    mystery: str
    repetition: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: str):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


ASP_RULES = r"""
mystery_item(X) :- mystery(X).
curious(C) :- child(C), curiosity(C).
repeats(C) :- child(C), repetition(C).
notice(C) :- child(C), repeats(C), near_banister(C).
solve(C) :- notice(C), mystery_item(X), found(X).
valid_story(P, M, R) :- beach(P), mystery(M), repetition(R).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("beach", "beach"),
    ]
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for rid in REPETITIONS:
        lines.append(asp.fact("repetition", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  only in python:", sorted(py - asp_set))
    print("  only in clingo:", sorted(asp_set - py))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in BEACHES:
        for m in MYSTERIES:
            for r in REPETITIONS:
                combos.append((place, m, r))
    return combos


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime beach story with a banister, curiosity, repetition, and a mystery to solve.")
    ap.add_argument("--place", choices=BEACHES.keys(), default="beach")
    ap.add_argument("--mystery", choices=MYSTERIES.keys())
    ap.add_argument("--repetition", choices=REPETITIONS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    place = args.place or "beach"
    mystery = args.mystery or rng.choice(sorted(MYSTERIES))
    repetition = args.repetition or rng.choice(sorted(REPETITIONS))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    child_type = "girl" if gender == "girl" else "boy"
    if place not in BEACHES:
        raise StoryError("This story only works at the beach.")
    return StoryParams(place=place, child_name=child_name, child_type=child_type, trait=trait, mystery=mystery, repetition=repetition)


def tell(params: StoryParams) -> World:
    world = World(params.place)
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name, meters={}, memes={}))
    parent = world.add(Entity(id="parent", kind="character", type="parent", label="Mom" if params.child_type == "girl" else "Dad", meters={}, memes={}))
    banister = world.add(Entity(id="banister", kind="thing", type="banister", label="banister", phrase="a smooth wooden banister by the boardwalk"))

    child.memes["curiosity"] = 1
    child.memes["repetition"] = 1

    world.say(f"At {BEACHES[params.place]['name']}, {child.label} was a {params.trait} little {params.child_type} who loved gentle questions.")
    world.say(f"Near the sand stood {banister.phrase}, and {child.label} kept looking at it as if it had a secret.")
    world.para()
    world.say(f"Every evening, {child.label} liked to {REPETITIONS[params.repetition]}.")
    world.say(f"{child.pronoun().capitalize()} would {REPETITIONS[params.repetition]} again, then again, listening to the hush of the waves and the small creak of wood.")
    world.para()
    mystery_text = MYSTERIES[params.mystery]
    world.say(f"One night, {child.label} noticed {mystery_text} tied to the banister.")
    world.say(f"{child.label} blinked. The little thing had not been there before, and now it seemed to glow in the moonlight.")
    world.say(f"{child.label} {REPETITIONS[params.repetition]} one more time, just to be sure, and that is when {child.pronoun('subject')} found a tiny tag: it belonged to a beach hut's lantern hook.")
    world.para()
    world.say(f"{parent.label} came closer and smiled. \"You solved the little mystery,\" {parent.pronoun()} said softly.")
    world.say(f"They carried {mystery_text} back to the hut, and {child.label} felt warm inside, like a shell held in a pocket.")
    world.say(f"After that, the banister was not strange anymore. It was just a friendly place to pause, count, and wonder before bedtime.")

    world.facts.update(
        child=child,
        parent=parent,
        banister=banister,
        mystery=params.mystery,
        repetition=params.repetition,
        place=params.place,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    p = world.facts["parent"]
    m = world.facts["mystery"]
    r = world.facts["repetition"]
    return [
        QAItem(
            question=f"Who was the story about at the beach?",
            answer=f"It was about {c.label}, a little curious child who kept noticing the banister by the water.",
        ),
        QAItem(
            question=f"What did {c.label} keep doing again and again?",
            answer=f"{c.label} kept {REPETITIONS[r]} because {c.pronoun('subject')} was curious and wanted to understand the strange little scene.",
        ),
        QAItem(
            question=f"What was the mystery to solve?",
            answer=f"The mystery was {MYSTERIES[m]}, which turned out to belong to a beach hut lantern hook.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"{c.label} looked closely, noticed the small tag, and then {p.label} helped carry {MYSTERIES[m]} back where it belonged.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a banister?",
            answer="A banister is a rail you can hold while walking up or down steps or along a walkway.",
        ),
        QAItem(
            question="Why do people repeat things when they are curious?",
            answer="People repeat things when they are curious because looking again can help them notice something they missed the first time.",
        ),
        QAItem(
            question="Why can a mystery feel exciting?",
            answer="A mystery can feel exciting because it gives you a little puzzle to think about until you discover the answer.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a bedtime story at the beach about {f['child'].label}, a child who is curious about a banister.",
        f"Tell a gentle story where repetition helps a little child solve a mystery near the boardwalk.",
        "Write a small bedtime story that begins with a curious look, repeats a comforting action, and ends with a solved mystery.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
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
    out.append("== (3) World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


CURATED = [
    StoryParams(place="beach", child_name="Mia", child_type="girl", trait="curious", mystery="shell", repetition="counting"),
    StoryParams(place="beach", child_name="Theo", child_type="boy", trait="gentle", mystery="rope", repetition="returning"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
            header = f"### {p.child_name}: beach / banister / {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
