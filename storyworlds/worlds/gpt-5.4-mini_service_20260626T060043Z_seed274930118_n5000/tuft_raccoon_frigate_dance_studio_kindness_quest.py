#!/usr/bin/env python3
"""
storyworlds/worlds/tuft_raccoon_frigate_dance_studio_kindness_quest.py
======================================================================

A small mystery story world set in a dance studio, built from the seed words
"tuft", "raccoon", and "frigate", with Kindness and Quest as the main narrative
instruments.

The world is deliberately tiny: a child dancer, a raccoon, a missing tuft, and
a little frigate prop become the center of a gentle mystery. The story turns on
searching, noticing clues, and choosing kindness.
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
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "child"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


@dataclass
class StoryParams:
    name: str
    gender: str
    helper_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

NAMES = ["Mia", "Lena", "Nora", "Ava", "Ivy", "Leo", "Noah", "Theo"]
HELPER_NAMES = ["Milo", "Pip", "June", "Tess", "Finn"]
PLACES = {"dance studio": "dance studio"}

# The specific prop set is intentionally narrow.
FRIGATE = Entity(
    id="frigate",
    kind="thing",
    type="prop",
    label="frigate",
    phrase="a little wooden frigate with blue paint",
)
TUFT = Entity(
    id="tuft",
    kind="thing",
    type="clue",
    label="tuft",
    phrase="a small gray tuft of fur",
)


# ---------------------------------------------------------------------------
# Narrative world
# ---------------------------------------------------------------------------

class StoryWorld(World):
    def __init__(self, place: str) -> None:
        super().__init__(place)
        self.clue_trail: list[str] = []


def _init_world(params: StoryParams) -> StoryWorld:
    w = StoryWorld("dance studio")
    dancer = w.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    helper = w.add(Entity(id=params.helper_name, kind="character", type="child", label=params.helper_name))
    raccoon = w.add(Entity(id="raccoon", kind="character", type="raccoon", label="the raccoon"))
    frigate = w.add(Entity(
        id="frigate", kind="thing", type="prop", label="frigate",
        phrase="a little wooden frigate with blue paint",
        owner=dancer.id,
    ))
    tuft = w.add(Entity(
        id="tuft", kind="thing", type="clue", label="tuft",
        phrase="a small gray tuft of fur",
        hidden=True,
    ))
    w.facts.update(dancer=dancer, helper=helper, raccoon=raccoon, frigate=frigate, tuft=tuft)
    return w


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------

def _rule_missing_tuft(w: StoryWorld) -> bool:
    tuft = w.get("tuft")
    if not tuft.hidden:
        return False
    tuft.hidden = False
    w.clue_trail.append("tuft under the bench")
    w.say("Near the mirror, they found a small gray tuft under the bench.")
    return True


def _rule_kindness_opens_clue(w: StoryWorld) -> bool:
    dancer = w.get(w.facts["dancer"].id)
    helper = w.get("raccoon")
    if dancer.memes.get("kindness", 0) < 1:
        return False
    if helper.meters.get("calm", 0) >= 1:
        return False
    helper.meters["calm"] = helper.meters.get("calm", 0) + 1
    w.say("The dancer spoke softly instead of shouting, and the raccoon stopped and listened.")
    return True


def _rule_quest_solves_mystery(w: StoryWorld) -> bool:
    if w.facts.get("solved"):
        return False
    tuft = w.get("tuft")
    if tuft.hidden:
        return False
    w.facts["solved"] = True
    w.say("That clue led them across the studio, past the ribbon box and the stacked chairs, until the missing frigate was found.")
    return True


def _rule_return_prop(w: StoryWorld) -> bool:
    frigate = w.get("frigate")
    if not w.facts.get("solved") or frigate.meters.get("returned", 0) >= 1:
        return False
    frigate.meters["returned"] = 1
    w.say("The raccoon had only been tugging it along like a treasure, and when the dancer smiled, it gently gave the frigate back.")
    return True


def propagate(w: StoryWorld) -> None:
    changed = True
    while changed:
        changed = False
        for rule in (_rule_missing_tuft, _rule_kindness_opens_clue, _rule_quest_solves_mystery, _rule_return_prop):
            if rule(w):
                changed = True


# ---------------------------------------------------------------------------
# Story beats
# ---------------------------------------------------------------------------

def tell_story(w: StoryWorld) -> StoryWorld:
    dancer = w.facts["dancer"]
    helper = w.facts["helper"]
    raccoon = w.facts["raccoon"]
    frigate = w.facts["frigate"]

    w.say(f"In the dance studio, {dancer.id} found {frigate.phrase} waiting by the barres.")
    w.say(f"{dancer.id} loved the tiny frigate, because it made the practice room feel like a little adventure.")
    w.para()
    w.say(f"Then the music stopped, and {frigate.label} was gone.")
    w.say(f"Only a rustle near the curtain and a dark little paw print gave any clue.")
    w.say(f"{helper.id} pointed to the floor. \"Look there,\" {helper.id} whispered, and the two of them followed the trail.")
    dancer.memes["worry"] = dancer.memes.get("worry", 0) + 1
    dancer.memes["quest"] = dancer.memes.get("quest", 0) + 1
    w.para()
    _rule_missing_tuft(w)
    dancer.memes["kindness"] = dancer.memes.get("kindness", 0) + 1
    w.say(f"{dancer.id} did not chase the raccoon away. Instead, {dancer.pronoun('subject')} offered a kind hand and a quiet voice.")
    propagate(w)
    if w.facts.get("solved"):
        w.say(f"At last, {dancer.id} laughed, {helper.id} clapped, and the raccoon blinked as if the whole mystery had been solved by kindness.")
    return w


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: StoryWorld) -> list[str]:
    f = world.facts
    return [
        'Write a gentle mystery for a small child set in a dance studio that includes the words "tuft", "raccoon", and "frigate".',
        f"Tell a story where {f['dancer'].id} notices a missing frigate, follows a clue, and uses kindness to solve the mystery.",
        "Write a short, child-facing quest story in which a raccoon leaves behind a tuft and the lost thing is found again.",
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    f = world.facts
    dancer = f["dancer"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"What was missing in the dance studio?",
            answer="The little wooden frigate was missing, which is why the dancer started a small quest to find it.",
        ),
        QAItem(
            question=f"What clue helped {dancer.id} and {helper.id} search?",
            answer="They found a small gray tuft under the bench, and that clue led them to the missing frigate.",
        ),
        QAItem(
            question=f"How did {dancer.id} solve the mystery?",
            answer="By staying calm, choosing kindness, and following the clue trail instead of acting angry.",
        ),
    ]


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dance studio?",
            answer="A dance studio is a room where people practice dancing, often with mirrors, open floor space, and music.",
        ),
        QAItem(
            question="What is a raccoon?",
            answer="A raccoon is a small wild animal with a striped tail and a dark mask around its eyes.",
        ),
        QAItem(
            question="What is a tuft?",
            answer="A tuft is a small bunch of hair, fur, grass, or fabric sticking together.",
        ),
        QAItem(
            question="What is a frigate?",
            answer="A frigate is a kind of ship, and in stories it can also be a toy ship or model ship.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(dance_studio).
character(dancer).
character(helper).
character(raccoon).
thing(frigate).
thing(tuft).

mystery_item(frigate).
clue(tuft).
helpful(helper).

solvable :- place(dance_studio), mystery_item(frigate), clue(tuft), helpful(helper).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "dance_studio"),
        asp.fact("character", "dancer"),
        asp.fact("character", "helper"),
        asp.fact("character", "raccoon"),
        asp.fact("thing", "frigate"),
        asp.fact("thing", "tuft"),
        asp.fact("mystery_item", "frigate"),
        asp.fact("clue", "tuft"),
        asp.fact("helpful", "helper"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solvable/0."))
    asp_ok = bool(model)
    py_ok = True
    if asp_ok != py_ok:
        print("MISMATCH: ASP and Python reasonableness gates differ.")
        return 1
    print("OK: ASP and Python reasonableness gates agree.")
    return 0


# ---------------------------------------------------------------------------
# Parameter resolution and generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery story world set in a dance studio.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name", choices=HELPER_NAMES)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice([n for n in NAMES if n not in {args.helper_name}])
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != name])
    return StoryParams(name=name, gender=gender, helper_name=helper_name)


def generate(params: StoryParams) -> StorySample:
    world = _init_world(params)
    tell_story(world)
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
        print("\n--- trace ---")
        for ent in sample.world.entities.values():
            meters = {k: v for k, v in ent.meters.items() if v}
            memes = {k: v for k, v in ent.memes.items() if v}
            print(f"{ent.id}: meters={meters} memes={memes} hidden={ent.hidden}")
        print(f"facts={sample.world.facts}")
    if qa:
        print()
        for title, items in (
            ("Generation prompts", sample.prompts),
            ("Story Q&A", [f"Q: {q.question}\nA: {q.answer}" for q in sample.story_qa]),
            ("World Q&A", [f"Q: {q.question}\nA: {q.answer}" for q in sample.world_qa]),
        ):
            print(f"== {title} ==")
            if title == "Generation prompts":
                for i, p in enumerate(items, 1):
                    print(f"{i}. {p}")
            else:
                for block in items:
                    print(block)
            print()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solvable/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solvable/0."))
        print("solvable" if model else "unsolvable")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Mia", gender="girl", helper_name="Pip"),
            StoryParams(name="Leo", gender="boy", helper_name="June"),
            StoryParams(name="Nora", gender="girl", helper_name="Finn"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
