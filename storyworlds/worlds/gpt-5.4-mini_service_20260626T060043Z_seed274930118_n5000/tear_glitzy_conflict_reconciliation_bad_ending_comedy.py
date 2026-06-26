#!/usr/bin/env python3
"""
storyworlds/worlds/.../tear_glitzy_conflict_reconciliation_bad_ending_comedy.py
==============================================================================

A small comedy-leaning story world about a glitzy outfit, an unlucky tear,
a squabbling pair, and a reconciliation that still ends a little badly.

Seed tale sketch:
---
A child loved a very glitzy cape made of shiny fabric. One day the cape tore
right before a little show. The child and a helper argued about what to do.
They tried to fix it, patched it badly, and went on anyway. The show was funny,
but the cape stayed torn, and everyone laughed through the awkward end.
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
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the little theater"
    indoors: bool = True
    affords: set[str] = field(default_factory=lambda: {"show", "fix"})


@dataclass
class HeroItem:
    label: str
    phrase: str
    region: str = "torso"


@dataclass
class Patch:
    label: str
    phrase: str


@dataclass
class StoryParams:
    place: str
    costume: str
    patch: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _r_tear(world: World) -> list[str]:
    out = []
    hero = world.entities.get("hero")
    costume = world.entities.get("costume")
    if not hero or not costume:
        return out
    if hero.memes.get("tugging", 0) < THRESHOLD:
        return out
    sig = ("tear", costume.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    costume.meters["torn"] = costume.meters.get("torn", 0) + 1
    costume.meters["messy"] = costume.meters.get("messy", 0) + 1
    return [f"The {costume.label} gave a tiny rip, then a very rude bigger rip."]


def _r_conflict(world: World) -> list[str]:
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    if not hero or not helper:
        return []
    if hero.memes.get("annoyed", 0) < THRESHOLD:
        return []
    sig = ("conflict", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
    return ["__conflict__"]


CAUSAL_RULES = [_r_tear, _r_conflict]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule(world)
            if bits:
                changed = True
                for b in bits:
                    if b != "__conflict__":
                        produced.append(b)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_world(params: StoryParams) -> World:
    world = World(Setting(place=params.place))
    hero = world.add(Entity(id="hero", kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=f"the {params.helper}"))
    costume = world.add(Entity(
        id="costume",
        type="thing",
        label=params.costume,
        phrase=f"a very {params.costume}",
        owner=hero.id,
        caretaker=helper.id,
    ))
    patch = world.add(Entity(
        id="patch",
        type="thing",
        label=params.patch,
        phrase=f"a {params.patch}",
        owner=helper.id,
    ))

    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {costume.label}; it was so glitzy it looked like a tiny disco ball in a cape.")
    world.say(f"{helper.label} carried {patch.phrase} and promised to help if anything went wrong.")
    world.para()

    hero.memes["joy"] = 1
    hero.memes["tugging"] = 1
    world.say(f"At {world.setting.place}, the little show began with a twirl, a bow, and one overexcited spin.")
    propagate(world)
    world.say(f"{hero.id} froze and stared at the rip. The {costume.label} still sparkled, but now it sparkled like it had lost an argument with a cat.")
    world.para()

    hero.memes["annoyed"] = 1
    world.say(f"{hero.id} wanted to blame somebody, and {helper.label} wanted to laugh first and fix second, which did not help.")
    propagate(world)
    world.say(f"They bickered for a moment about who should hold the torn seam, which was a very serious problem for a very ridiculous minute.")
    world.para()

    hero.memes["reconciling"] = 1
    helper.memes["reconciling"] = 1
    world.say(f"Then {helper.label} softened and said, \"Okay, let's patch it together.\"")
    world.say(f"{hero.id} nodded, still frowning, because that was the most polite grumpy face {hero.id} could make.")
    world.say(f"They pressed on the patch, but it stuck crookedly and left a lumpy square right on the shiny spot.")
    world.say(f"So the two of them made up, laughed at the lopsided patch, and went back out anyway.")
    world.say(f"The show ended with applause, a crooked costume, and {hero.id} doing a bow so dramatic it nearly caused another tear.")
    world.say(f"Everyone laughed, because the ending was a little bad, but in the funniest possible way.")

    world.facts.update(
        hero=hero,
        helper=helper,
        costume=costume,
        patch=patch,
        setting=world.setting,
        conflict=True,
        reconciled=True,
        bad_ending=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short comedy story about a glitzy costume that gets a tear during a show.',
        f"Tell a funny story where {f['hero'].id} and {f['helper'].label} argue, then reconcile, but the fix is still imperfect.",
        f"Write a child-friendly story with a glitzy thing, a tear, and a bad ending that still feels amusing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    costume = f["costume"]
    return [
        QAItem(
            question=f"What did {hero.id} love at the start of the story?",
            answer=f"{hero.id} loved {hero.pronoun('possessive')} {costume.label}, which was so glitzy it looked like a tiny disco ball in a cape.",
        ),
        QAItem(
            question=f"What went wrong during the show at {world.setting.place}?",
            answer=f"The {costume.label} tore during a twirl, so the shiny outfit got damaged right in the middle of the show.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.label} stop arguing?",
            answer=f"They reconciled by deciding to patch the tear together, even though the fix came out crooked.",
        ),
        QAItem(
            question=f"Why is the ending a bad ending, even though everyone laughed?",
            answer=f"The ending is bad because the {costume.label} stayed lumpy and torn-looking, but it was funny because everyone kept going anyway.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "tear": [
        QAItem(
            question="What is a tear in cloth?",
            answer="A tear is a rip or split in fabric that makes a piece of clothing damaged.",
        )
    ],
    "glitzy": [
        QAItem(
            question="What does glitzy mean?",
            answer="Glitzy means shiny, flashy, and attention-grabbing, like something made to sparkle on purpose.",
        )
    ],
    "reconciliation": [
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop fighting and make peace again.",
        )
    ],
    "comedy": [
        QAItem(
            question="What makes a story feel like comedy?",
            answer="A comedy story tries to make people laugh with silly trouble, awkward moments, or funny surprises.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [qa for key in ["tear", "glitzy", "reconciliation", "comedy"] for qa in WORLD_KNOWLEDGE[key]]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


NAMES_GIRL = ["Maya", "Lina", "Zoe", "Nina", "Ruby"]
NAMES_BOY = ["Leo", "Finn", "Theo", "Max", "Eli"]
HELPERS = ["parent", "aunt", "uncle", "friend"]
COSTUMES = [
    HeroItem(label="glitzy cape", phrase="a very glitzy cape"),
    HeroItem(label="glitzy jacket", phrase="a very glitzy jacket"),
    HeroItem(label="glitzy skirt", phrase="a very glitzy skirt"),
]
PATCHES = [
    Patch(label="gold patch", phrase="a gold patch"),
    Patch(label="sparkly tape", phrase="sparkly tape"),
    Patch(label="silver patch", phrase="a silver patch"),
]


@dataclass
class StoryChoice:
    place: str = "the little theater"
    costume: str = "glitzy cape"
    patch: str = "gold patch"
    name: str = "Maya"
    gender: str = "girl"
    helper: str = "parent"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy story world with a glitzy tear, conflict, reconciliation, and a bad ending.")
    ap.add_argument("--place", default="the little theater")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--helper", choices=HELPERS, default=None)
    ap.add_argument("--costume", choices=[c.label for c in COSTUMES], default=None)
    ap.add_argument("--patch", choices=[p.label for p in PATCHES], default=None)
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
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    costume = args.costume or rng.choice([c.label for c in COSTUMES])
    patch = args.patch or rng.choice([p.label for p in PATCHES])
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=args.place, costume=costume, patch=patch, name=name, gender=gender, helper=helper)


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


ASP_RULES = r"""
glitzy(costume).
tear_event(costume) :- glitzy(costume).
conflict(hero,helper) :- tear_event(costume).
reconciled(hero,helper) :- conflict(hero,helper).
bad_ending(costume) :- reconciled(hero,helper), tear_event(costume).
#show glitzy/1.
#show tear_event/1.
#show conflict/2.
#show reconciled/2.
#show bad_ending/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("glitzy", "costume"),
        asp.fact("setting", "theater"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show bad_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for i, costume in enumerate(COSTUMES):
            params = StoryParams(
                place=args.place,
                costume=costume.label,
                patch=PATCHES[i % len(PATCHES)].label,
                name=NAMES_GIRL[i % len(NAMES_GIRL)],
                gender="girl" if i % 2 == 0 else "boy",
                helper=HELPERS[i % len(HELPERS)],
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
