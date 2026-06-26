#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/institute_stack_outing_suspense_mystery.py
===============================================================================================================

A small storyworld in a suspenseful, mystery-like institute setting.

Premise:
- A child visits an institute on an outing.
- A stack of papers, crates, or books goes missing or seems wrong.
- The suspense comes from a careful search, clues, and a reveal.
- The ending proves what changed: the stack is found, sorted, or restored.

This world keeps the prose child-facing and concrete while the simulated state
drives the story beats.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the institute"
    indoors: bool = True


@dataclass
class StackItem:
    id: str
    label: str
    phrase: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    stack: str
    outing: str
    name: str
    gender: str
    guide: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes["unease"] < THRESHOLD:
            continue
        sig = ("worry", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"{ent.label or ent.id} kept looking around with a worried face.")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("clue_found") and world.facts.get("missing_stack"):
        sig = ("reveal", world.facts["missing_stack"])
        if sig in world.fired:
            return out
        world.fired.add(sig)
        out.append("__reveal__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_worry, _r_reveal):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__reveal__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "institute": Setting(place="the institute", indoors=True),
    "archive": Setting(place="the institute archive", indoors=True),
    "museum": Setting(place="the institute museum room", indoors=True),
}

STACKS = {
    "books": StackItem(id="books", label="stack of books", phrase="a tall stack of old books", plural=True),
    "papers": StackItem(id="papers", label="stack of papers", phrase="a neat stack of papers", plural=True),
    "boxes": StackItem(id="boxes", label="stack of boxes", phrase="a wobbly stack of small boxes", plural=True),
}

OUTINGS = {
    "tour": {
        "verb": "take a quiet tour",
        "gerund": "taking a quiet tour",
        "reason": "to learn the institute's rooms",
        "clue": "a scrap of paper",
        "mystery": "who moved the stack",
    },
    "visit": {
        "verb": "visit the exhibit",
        "gerund": "visiting the exhibit",
        "reason": "to see the curious things inside",
        "clue": "a blue tag",
        "mystery": "where the stack had gone",
    },
    "outing": {
        "verb": "go on an outing",
        "gerund": "going on an outing",
        "reason": "to explore the institute together",
        "clue": "a small map",
        "mystery": "why the stack looked wrong",
    },
}

GIRL_NAMES = ["Mia", "Lena", "Nora", "Ava", "Iris", "Zoe"]
BOY_NAMES = ["Leo", "Finn", "Milo", "Eli", "Theo", "Owen"]
TRAITS = ["curious", "quiet", "careful", "brave", "thoughtful", "patient"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Suspenseful institute outing mystery storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--stack", choices=STACKS)
    ap.add_argument("--outing", choices=OUTINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--guide", choices=["librarian", "curator", "teacher"])
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for stack in STACKS:
            for outing in OUTINGS:
                combos.append((place, stack, outing))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.stack is None or c[1] == args.stack)
              and (args.outing is None or c[2] == args.outing)]
    if not combos:
        raise StoryError("No valid institute outing setup matches those options.")
    place, stack, outing = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide = args.guide or rng.choice(["librarian", "curator", "teacher"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, stack=stack, outing=outing, name=name, gender=gender, guide=guide, trait=trait)


def search_story(world: World, hero: Entity, guide: Entity, stack: Entity, outing: dict) -> None:
    hero.memes["curiosity"] += 1
    hero.memes["unease"] += 1
    world.say(f"{hero.id} was a {hero.trait} {hero.type} who loved quiet places and small mysteries.")
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {guide.label} went to {world.setting.place} for an outing.")
    world.say(f"They were {outing['gerund']} because {outing['reason']}.")
    world.say(f"Near the reading table stood {stack.phrase}, and everyone agreed it should stay straight and tidy.")

    world.para()
    stack.meters["tipped"] += 1
    hero.memes["unease"] += 1
    world.say(f"Then the room went still. The {stack.label} looked wrong, as if one book had slipped out of place.")
    world.say(f"{hero.id} noticed the little gap first and held {hero.pronoun('possessive')} breath.")
    world.say(f'"Something does not fit," {hero.pronoun()} whispered.')

    world.para()
    world.say(f"{guide.id} did not rush. Instead, {guide.pronoun()} pointed to a tiny clue: {outing['clue']}.")
    world.say(f"{hero.id} followed it past a shelf, then under a bench, and found the missing piece hiding there.")
    world.facts["clue_found"] = True
    world.facts["missing_stack"] = stack.id
    propagate(world, narrate=True)

    world.para()
    stack.meters["tipped"] = 0
    stack.memes["order"] += 1
    hero.memes["unease"] = 0
    hero.memes["relief"] += 1
    world.say(f"Together they set the {stack.label} back in order.")
    world.say(f"At the end of the outing, {hero.id} smiled at the neat stack, and the mystery felt small and solved.")


def generate_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=[params.trait], label=params.name))
    hero.trait = params.trait  # child-facing world facts, not shown directly except in narration
    guide = world.add(Entity(id="Guide", kind="character", type=params.guide, label=f"the {params.guide}"))
    stack_cfg = STACKS[params.stack]
    stack = world.add(Entity(id=stack_cfg.id, type="stack", label=stack_cfg.label, phrase=stack_cfg.phrase, plural=stack_cfg.plural))
    world.facts.update(hero=hero, guide=guide, stack=stack, outing=OUTINGS[params.outing], params=params)
    search_story(world, hero, guide, stack, OUTINGS[params.outing])
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, guide, stack, outing = f["hero"], f["guide"], f["stack"], f["outing"]
    return [
        f'Write a suspenseful mystery story for a young child about an outing to {world.setting.place}.',
        f"Tell a gentle mystery where {hero.id} and {guide.label} notice that the {stack.label} looks wrong during an outing.",
        f'Write a short story that includes the words "institute", "stack", and "outing" and ends with the mystery solved.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, guide, stack, outing = f["hero"], f["guide"], f["stack"], f["outing"]
    return [
        QAItem(
            question=f"Where did {hero.id} go on the outing?",
            answer=f"{hero.id} went to {world.setting.place} with {guide.label} for an outing.",
        ),
        QAItem(
            question=f"What made the room feel mysterious?",
            answer=f"The {stack.label} looked wrong, and {hero.id} noticed a missing piece near the stack.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"{hero.id} followed a tiny clue, found the missing piece, and helped set the {stack.label} back in order.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an institute?",
            answer="An institute is a place where people learn, study, or keep special things in an organized way.",
        ),
        QAItem(
            question="What is a stack?",
            answer="A stack is a pile of things placed one on top of another.",
        ),
        QAItem(
            question="What is an outing?",
            answer="An outing is a trip out to do something fun, learn something, or visit a place.",
        ),
        QAItem(
            question="What does suspense mean in a story?",
            answer="Suspense is the feeling that something important or mysterious is about to be found out.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world knowledge ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/3.

valid(P,S,O) :- place(P), stack(S), outing(O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for s in STACKS:
        lines.append(asp.fact("stack", s))
    for o in OUTINGS:
        lines.append(asp.fact("outing", o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(place="institute", stack="books", outing="tour", name="Mia", gender="girl", guide="librarian", trait="curious"),
    StoryParams(place="archive", stack="papers", outing="visit", name="Leo", gender="boy", guide="curator", trait="careful"),
    StoryParams(place="museum", stack="boxes", outing="outing", name="Nora", gender="girl", guide="teacher", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.stack} at {p.place} ({p.outing})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
