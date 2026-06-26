#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/duplo_jewish_claim_dialogue_fable.py
===============================================================================================================

A small, self-contained story world about a Jewish family room, a box of duplo
bricks, and a fable-like lesson about making a fair claim.

Seed tale:
---
At a Jewish family evening, two children found a bright box of duplo bricks.
One child claimed the red bridge first, then the other claimed the blue tower.
Their grandmother listened, asked them to speak kindly, and suggested they
build together: one child could claim the red bricks for the roof, and the other
could claim the blue bricks for the road. The children agreed, laughed, and made
a castle bigger than either one could have made alone.

World premise:
- A claim is a spoken attempt to own a toy part or turn.
- Duplo bricks are physical objects that can be held, stacked, and put into
  bundles.
- A Jewish family setting adds a warm, shared-meal, shared-lesson mood.
- Dialogue drives the turn from selfish claiming to fair sharing.
- The ending should prove the change in state: a joint build, settled feelings,
  and an explicit fable-like moral.

This script follows the storyworld contract and supports:
default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify,
and --show-asp.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Toy:
    id: str
    label: str
    phrase: str
    region: str
    is_duplo: bool = False
    plural: bool = False
    colors: set[str] = field(default_factory=set)


@dataclass
class Claim:
    id: str
    label: str
    phrase: str
    requires: set[str] = field(default_factory=set)
    result: str = ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    setting: str
    child1: str
    child2: str
    toy: str
    claim: str
    claim_word: str
    seed: Optional[int] = None


SETTINGS = {
    "family_table": Setting(
        place="the family table",
        mood="warm",
        affords={"duplo_build", "dialogue", "sharing"},
    ),
    "community_room": Setting(
        place="the Jewish community room",
        mood="busy",
        affords={"duplo_build", "dialogue", "sharing"},
    ),
    "sunny_patio": Setting(
        place="the sunny patio",
        mood="bright",
        affords={"duplo_build", "dialogue", "sharing"},
    ),
}

CHILDREN = [
    ("Ari", "boy"),
    ("Mina", "girl"),
    ("Leah", "girl"),
    ("Noam", "boy"),
    ("Tali", "girl"),
    ("Eli", "boy"),
]

TOYS = {
    "duplo_bridge": Toy(
        id="duplo_bridge",
        label="duplo bricks",
        phrase="a box of bright duplo bricks",
        region="hands",
        is_duplo=True,
        plural=True,
        colors={"red", "blue", "yellow", "green"},
    ),
    "duplo_tower": Toy(
        id="duplo_tower",
        label="duplo bricks",
        phrase="a box of bright duplo bricks",
        region="hands",
        is_duplo=True,
        plural=True,
        colors={"red", "blue", "yellow", "green"},
    ),
}

CLAIMS = {
    "first_claim": Claim(
        id="first_claim",
        label="first claim",
        phrase="claimed the biggest red bricks first",
        requires={"duplo_build"},
        result="one child gets the first turn",
    ),
    "color_claim": Claim(
        id="color_claim",
        label="color claim",
        phrase="claimed the blue bricks for a tower",
        requires={"duplo_build"},
        result="one child gets a color section",
    ),
    "shared_claim": Claim(
        id="shared_claim",
        label="shared claim",
        phrase="claimed a fair share and invited help",
        requires={"sharing"},
        result="both children get a fair share",
    ),
}

KNOWLEDGE = {
    "duplo": [
        (
            "What are duplo bricks?",
            "Duplo bricks are big building blocks made for small hands, so children can stack and connect them easily.",
        )
    ],
    "claim": [
        (
            "What does it mean to claim something?",
            "To claim something is to say that you want it or that it should be yours, often before other people decide together.",
        )
    ],
    "jewish": [
        (
            "What does Jewish mean?",
            "Jewish means connected to the Jewish people, their families, traditions, and community life.",
        )
    ],
    "sharing": [
        (
            "Why is sharing helpful?",
            "Sharing helps people take turns, avoid fights, and enjoy making or playing together.",
        )
    ],
}

KNOWLEDGE_ORDER = ["jewish", "duplo", "claim", "sharing"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c1, t1 in CHILDREN:
            for c2, t2 in CHILDREN:
                if c1 == c2:
                    continue
                for toy in TOYS:
                    for cl in CLAIMS:
                        combos.append((s, f"{c1}:{t1}", f"{c2}:{t2}:{toy}:{cl}"))
    return combos


def make_world(setting: Setting, child1: tuple[str, str], child2: tuple[str, str], toy: Toy, claim: Claim) -> World:
    w = World(setting)
    a = w.add(Entity(id=child1[0], kind="character", type=child1[1], label=child1[0]))
    b = w.add(Entity(id=child2[0], kind="character", type=child2[1], label=child2[0]))
    t = w.add(Entity(id=toy.id, type="toy", label=toy.label, phrase=toy.phrase, plural=toy.plural))
    w.facts.update(a=a, b=b, toy=t, claim=claim, toy_cfg=toy, setting=setting)
    return w


def _init_emotions(w: World) -> None:
    for e in w.characters():
        e.memes.setdefault("joy", 0.0)
        e.memes.setdefault("irritation", 0.0)
        e.memes.setdefault("fairness", 0.0)
        e.memes.setdefault("pride", 0.0)
        e.meters.setdefault("held", 0.0)


def _claim_tension(w: World, claimer: Entity, other: Entity, toy: Entity, claim: Claim) -> None:
    sig = ("claim_tension", claimer.id, claim.id)
    if sig in w.fired:
        return
    w.fired.add(sig)
    claimer.memes["pride"] += 1
    other.memes["irritation"] += 1
    w.say(f'{claimer.id} said, "I claim the {toy.label}!"')


def _dialogue_turn(w: World, a: Entity, b: Entity, toy: Entity) -> None:
    sig = ("dialogue_turn", a.id, b.id)
    if sig in w.fired:
        return
    w.fired.add(sig)
    w.say(f'{b.id} answered, "But I found it first."')
    w.say(f'The room grew quiet, and the bright {toy.label} waited between them.')


def _elder_guidance(w: World, elder: Entity, a: Entity, b: Entity, toy: Entity, claim: Claim) -> None:
    sig = ("elder", elder.id)
    if sig in w.fired:
        return
    w.fired.add(sig)
    a.memes["irritation"] += 0.5
    b.memes["irritation"] += 0.5
    w.say(
        f'{elder.id} said, "A fair claim is not a loud one. '
        f'First ask, then build, and the bricks can answer for both of you."'
    )
    w.say(f'{elder.id} pointed at the {toy.label} and smiled at the little builders.')


def _share_build(w: World, a: Entity, b: Entity, toy: Entity, claim: Claim) -> None:
    sig = ("share_build", claim.id)
    if sig in w.fired:
        return
    w.fired.add(sig)
    a.memes["fairness"] += 1
    b.memes["fairness"] += 1
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    a.meters["held"] += 1
    b.meters["held"] += 1
    w.say(f'Then {a.id} said, "You can use the blue bricks."')
    w.say(f'{b.id} replied, "And you can take the red ones."')
    w.say(f'At last they built one duplo house together, taller and brighter than before.')


def _moral(w: World, a: Entity, b: Entity) -> None:
    sig = ("moral",)
    if sig in w.fired:
        return
    w.fired.add(sig)
    w.say(
        f'The children learned that a claim made with kind words can become a '
        f'shared joy, and the best prize is often the one both hands can help make.'
    )


def tell(setting: Setting, child1: tuple[str, str], child2: tuple[str, str], toy: Toy, claim: Claim) -> World:
    w = make_world(setting, child1, child2, toy, claim)
    _init_emotions(w)
    a = w.get(child1[0])
    b = w.get(child2[0])
    elder = w.add(Entity(id="Grandmother", kind="character", type="grandmother", label="Grandmother"))
    toy_entity = w.get(toy.id)

    w.say(
        f'At {setting.place}, under a {setting.mood} light, {a.id} and {b.id} '
        f'found {toy.phrase}.'
    )
    w.say(
        f'It was a Jewish family day, and the duplo bricks looked as if they were '
        f'waiting for a story.'
    )
    w.para()
    _claim_tension(w, a, b, toy_entity, claim)
    _dialogue_turn(w, a, b, toy_entity)
    _elder_guidance(w, elder, a, b, toy_entity, claim)
    w.para()
    _share_build(w, a, b, toy_entity, claim)
    _moral(w, a, b)
    w.facts.update(resolved=True, elder=elder, moral="shared joy")
    return w


def story_prompt(world: World) -> list[str]:
    f = world.facts
    a, b, toy, claim = f["a"], f["b"], f["toy_cfg"], f["claim"]
    return [
        f'Write a short fable for children about {a.id} and {b.id} at {world.setting.place} '
        f'who argue over {toy.phrase} and learn a fair claim.',
        f'Compose a dialogue-heavy story with Jewish family warmth, duplo bricks, and a lesson about '
        f'{claim.label}.',
        f'Write a gentle fable where two children speak kindly, share {toy.label}, and end with a moral.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, toy, claim = f["a"], f["b"], f["toy_cfg"], f["claim"]
    return [
        QAItem(
            question=f"What did {a.id} and {b.id} find at {world.setting.place}?",
            answer=f"They found {toy.phrase} and both wanted a piece of it.",
        ),
        QAItem(
            question=f"What did {a.id} say when the argument started?",
            answer=f'{a.id} said, "I claim the {toy.label}!"',
        ),
        QAItem(
            question=f'How did Grandmother help with the {claim.label}?',
            answer='She asked them to speak kindly, take turns, and make one shared build instead of fighting.',
        ),
        QAItem(
            question="What did they build at the end?",
            answer="They built one duplo house together, and it was taller and brighter than before.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"duplo", "claim", "jewish", "sharing"}
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def generation_prompts(world: World) -> list[str]:
    return story_prompt(world)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
claim_tension(A) :- claim_attempt(A).
dialogue_turn(A,B) :- claim_tension(A), other(B).
resolved :- dialogue_turn(A,B), elder_guidance, shared_build.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c, _ in CHILDREN:
        lines.append(asp.fact("child", c))
    for t in TOYS:
        lines.append(asp.fact("toy", t))
    for cl in CLAIMS:
        lines.append(asp.fact("claim", cl))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A dialogue-driven fable about duplo, Jewish family life, and fair claims.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--claim", choices=CLAIMS)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    toy = args.toy or rng.choice(list(TOYS))
    claim = args.claim or rng.choice(list(CLAIMS))
    c1 = args.name1 or rng.choice([n for n, _ in CHILDREN])
    c2 = args.name2 or rng.choice([n for n, _ in CHILDREN if n != c1])
    if c1 == c2:
        raise StoryError("The two children must be different.")
    return StoryParams(setting=setting, child1=c1, child2=c2, toy=toy, claim=claim, claim_word="claim")


def generate(params: StoryParams) -> StorySample:
    child_map = {n: t for n, t in CHILDREN}
    world = tell(
        SETTINGS[params.setting],
        (params.child1, child_map[params.child1]),
        (params.child2, child_map[params.child2]),
        TOYS[params.toy],
        CLAIMS[params.claim],
    )
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for parity scaffolding in this world.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for s in SETTINGS:
            for toy in TOYS:
                for claim in CLAIMS:
                    params = StoryParams(setting=s, child1="Ari", child2="Mina", toy=toy, claim=claim, claim_word="claim")
                    samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            sample = generate(p)
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
