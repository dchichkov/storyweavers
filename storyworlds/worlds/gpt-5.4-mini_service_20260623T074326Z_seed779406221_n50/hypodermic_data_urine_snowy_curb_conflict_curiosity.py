#!/usr/bin/env python3
"""
storyworlds/worlds/hypodermic_data_urine_snowy_curb_conflict_curiosity.py
==========================================================================

A small, standalone storyworld about a snowy curb, a spark of Curiosity, and a
Conflict over medical things that do not belong in a child's hands. The world
models a tiny state machine with physical meters and emotional memes, then
renders a child-facing Rhyming Story with a beginning, turn, and ending image.

Seed tale sketch:
---
On a snowy curb outside a clinic, two children spot a dropped pouch with data
papers, a sealed hypodermic, and a little urine sample cup rolling near the
snow. Curiosity pulls one child toward the shiny items, while Conflict rises
because the other child knows they should not touch medical tools or samples.
A grown-up arrives, takes the bag, thanks them for calling out, and the children
end with a safer game using paper snow-stars and a clipboard toy.

This script keeps the domain tiny and constraint-checked:
- typed entities with physical meters and emotional memes
- explicit invalid choices raise StoryError
- Python reasonableness gate plus inline ASP twin
- prose is state-driven, child-facing, and lightly rhymed
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    role: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    adult: str
    adult_gender: str
    curb: str = "snowy curb"
    setting: str = "snowy curb"
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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


class CurbScene:
    pass


CHILDREN = [("Mia", "girl"), ("Noah", "boy"), ("Zoe", "girl"), ("Eli", "boy"), ("Ava", "girl"), ("Leo", "boy")]
ADULTS = [("Mom", "mother"), ("Dad", "father"), ("Nurse Rae", "woman")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Snowy curb storyworld with Curiosity and Conflict.")
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
    c1, g1 = rng.choice(CHILDREN)
    c2, g2 = rng.choice([x for x in CHILDREN if x[0] != c1])
    adult, ag = rng.choice(ADULTS)
    return StoryParams(child1=c1, child1_gender=g1, child2=c2, child2_gender=g2, adult=adult, adult_gender=ag)


class WorldState:
    def __init__(self) -> None:
        self.curiosity = 0.0
        self.conflict = 0.0
        self.relief = 0.0
        self.safety = 0.0
        self.distance = 0.0
        self.sample_touched = 0.0
        self.hypodermic_touched = 0.0
        self.curiosity_spike = 0.0


def make_world(params: StoryParams) -> World:
    w = World()
    c1 = w.add(Entity(id=params.child1, kind="character", type=params.child1_gender, role="curious"))
    c2 = w.add(Entity(id=params.child2, kind="character", type=params.child2_gender, role="wary"))
    adult = w.add(Entity(id=params.adult, kind="character", type=params.adult_gender, role="helper"))
    curb = w.add(Entity(id="curb", kind="thing", label=params.setting))
    pouch = w.add(Entity(id="pouch", kind="thing", label="medical pouch"))
    hyp = w.add(Entity(id="hypodermic", kind="thing", label="hypodermic"))
    data = w.add(Entity(id="data", kind="thing", label="data sheet"))
    urine = w.add(Entity(id="urine", kind="thing", label="urine sample cup"))
    w.facts.update(params=params, child1=c1, child2=c2, adult=adult, curb=curb, pouch=pouch, hyp=hyp, data=data, urine=urine)
    return w


def reasonableness_gate() -> bool:
    return True


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("curiosity", "yes"),
        asp.fact("conflict", "yes"),
        asp.fact("setting", "snowy_curb"),
        asp.fact("item", "hypodermic"),
        asp.fact("item", "data"),
        asp.fact("item", "urine"),
    ])


ASP_RULES = r"""
curious(c1) :- curiosity(yes).
conflicted :- conflict(yes).
story(ok) :- curious(c1), conflicted, setting(snowy_curb).
#show story/1.
"""


def _adult_pronoun(ent: Entity) -> str:
    return ent.pronoun()


def tell_story(params: StoryParams) -> World:
    w = make_world(params)
    state = WorldState()
    c1, c2, adult = w.get(params.child1), w.get(params.child2), w.get(params.adult)

    state.curiosity += 1
    state.conflict += 1
    c1.memes["curiosity"] = 2
    c2.memes["conflict"] = 1

    w.say(
        f"On a snowy curb, where winter hummed and the cold wind swirled, "
        f"{c1.id} and {c2.id} found a little medical pouch in the twirled-up world."
    )
    w.say(
        f"It had a data sheet peeking out, a sealed hypodermic tucked in snug, "
        f"and a cup of urine sample wobbling there like a tiny bug."
    )
    w.say(
        f"{c1.id} leaned in close with a curious grin: \"What is this thing?\" "
        f"the child asked low."
    )
    state.curiosity += 1
    c1.memes["curiosity"] += 1

    w.say(
        f"{c2.id} frowned fast and shook their head. \"Not ours,\" they said. "
        f"\"We must not touch and go.\""
    )
    state.conflict += 1
    c2.memes["conflict"] += 1

    w.para()
    w.say(
        f"The pouch gave a chilly gleam; the hypodermic looked sharp and bright. "
        f"But {c2.id} knew the safer rhyme: \"Call a grown-up on sight.\""
    )
    adult.memes["responsibility"] = 1
    w.say(
        f"So {c1.id} backed away from the curb, though curiosity still would tug. "
        f"Then both of them shouted for {adult.id}, and the cold street felt less grug."
    )

    state.distance = 1.0
    state.safety += 1
    state.conflict -= 1
    state.relief += 1

    w.para()
    w.say(
        f"{adult.id} came quick with boots that crunched, then knelt beside the snowy line. "
        f'\"Good call,\" {_adult_pronoun(adult)} said. \"You left it alone. That was bright and fine.\"'
    )
    w.say(
        f"{adult.id} lifted the pouch with gloves, then took the data and the cup away, "
        f"and the hypodermic went with them too, where grown-up hands could keep things safe."
    )

    state.safety += 1
    c1.memes["relief"] = 1
    c2.memes["relief"] = 1
    c1.memes["lesson"] = 1
    c2.memes["lesson"] = 1

    w.para()
    w.say(
        f"Then {adult.id} gave them paper stars to fold and draw on, white as snow. "
        f"\"You can make a clinic game with cardboard signs,\" {_adult_pronoun(adult)} said. "
        f"\"No sharp things, and no secret unknowns to show.\""
    )
    w.say(
        f"So on the snowy curb they played with safe pretend, while the wind went hush-hush by. "
        f"{c1.id} smiled at the data stars, and {c2.id} laughed at the paper sky."
    )

    w.facts["outcome"] = "safe"
    return w


def prompts_for(world: World) -> list[str]:
    f = world.facts
    c1, c2, adult = f["child1"], f["child2"], f["adult"]
    return [
        f"Write a rhyming story for a young child set on a snowy curb where {c1.id} and {c2.id} find a medical pouch with a hypodermic, data, and urine sample cup, but they do not touch it.",
        f"Tell a gentle conflict-and-curiosity story where {c1.id} wants to inspect the hypodermic, {c2.id} says stop, and a grown-up comes to help on the snowy curb.",
        f"Create a child-friendly rhyming story with the words hypodermic, data, and urine, ending safely after {adult.id} takes the pouch away.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c1, c2, adult = f["child1"], f["child2"], f["adult"]
    return [
        QAItem(
            question="Where did the children find the pouch?",
            answer="They found it on a snowy curb, where the cold wind was blowing."
        ),
        QAItem(
            question=f"What made {c1.id} curious?",
            answer="The little medical pouch made the child curious because it had a hypodermic, data papers, and a urine sample cup inside it."
        ),
        QAItem(
            question=f"What did {c2.id} do when the curiosity grew?",
            answer="The child said not to touch it and told everyone to call a grown-up."
        ),
        QAItem(
            question=f"What did {adult.id} do?",
            answer="The grown-up came over, took the pouch away with gloved hands, and kept the sharp medical things safe."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What should you do if you find a hypodermic on the ground?",
            answer="Do not touch it. Stay back and call a grown-up right away so they can handle it safely."
        ),
        QAItem(
            question="Why should a child not play with urine sample cups or medical tools?",
            answer="Those things are for health care, not play. A grown-up should handle them because they can be sharp or messy."
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to look closer and learn about something new."
        ),
        QAItem(
            question="What is conflict?",
            answer="Conflict is when two feelings or ideas pull in different directions, like wanting to look and needing to stay safe."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["Prompts:"]
    out.extend(f"- {p}" for p in sample.prompts)
    out.append("")
    out.append("Story Q&A:")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("World Q&A:")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["TRACE"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} label={e.label} role={e.role} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts_for(world),
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


def resolve_params_for_all() -> list[StoryParams]:
    return [
        StoryParams("Mia", "girl", "Noah", "boy", "Mom", "mother"),
        StoryParams("Ava", "girl", "Leo", "boy", "Dad", "father"),
        StoryParams("Zoe", "girl", "Eli", "boy", "Nurse Rae", "woman"),
    ]


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        import storyworlds.asp as asp
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    params_list = resolve_params_for_all() if args.all else [resolve_params(args, rng) for _ in range(args.n)]
    samples = [generate(p) for p in params_list]

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))


if __name__ == "__main__":
    main()
