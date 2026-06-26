#!/usr/bin/env python3
"""
A small detective-story world about a child investigator, a red spill of koolaid,
and a misunderstanding that ends in reconciliation and practical problem solving.

Seed tale:
---
Behold, the kitchen floor was red with koolaid. Mina thought someone had done a
mean trick, but the clues pointed to a tipped cup, not a prank. She followed the
drips, asked careful questions, and found out her brother had been trying to help
with the snacks. Together they cleaned the mess, fixed the broken rule, and made
peace before the cookies were served.
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
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the kitchen"
    affords: set[str] = field(default_factory=lambda: {"koolaid"})

    mood: str = "busy"


@dataclass
class Mystery:
    id: str
    clue: str
    spill: str
    stain: str
    cause: str
    method: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
    ally: str
    role: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"koolaid"}, mood="busy"),
    "hallway": Setting(place="the hallway", affords={"koolaid"}, mood="quiet"),
    "classroom": Setting(place="the classroom", affords={"koolaid"}, mood="busy"),
}

MYSTERIES = {
    "spill": Mystery(
        id="spill",
        clue="red drips",
        spill="koolaid",
        stain="red stain",
        cause="a tipped cup",
        method="cleaning the floor",
        tags={"koolaid", "clue", "stain"},
    ),
    "tablecloth": Mystery(
        id="tablecloth",
        clue="wet corners",
        spill="koolaid",
        stain="sticky red marks",
        cause="a cup knocked by an elbow",
        method="washing the cloth",
        tags={"koolaid", "clue", "stain"},
    ),
}

NAMES = {
    "girl": ["Mina", "June", "Ivy", "Nora", "Lily"],
    "boy": ["Leo", "Owen", "Theo", "Max", "Eli"],
}

ROLES = ["sister", "brother", "friend", "cousin", "neighbor"]

CHARACTER_TYPES = {
    "sister": "girl",
    "brother": "boy",
    "friend": "boy",
    "cousin": "girl",
    "neighbor": "boy",
}


# ---------------------------------------------------------------------------
# Narrative model
# ---------------------------------------------------------------------------
def setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    ally = world.add(Entity(id="ally", kind="character", type=CHARACTER_TYPES[params.ally], label=params.ally))
    mystery = MYSTERIES[params.mystery]
    stain = world.add(Entity(id="stain", type="thing", label=mystery.stain, phrase=mystery.stain, owner=hero.id))
    world.facts.update(hero=hero, ally=ally, mystery=mystery, stain=stain)
    return world


def introduce(world: World) -> None:
    hero: Entity = world.facts["hero"]
    world.say(
        f"{hero.id} was a little detective who noticed tiny details, even when the room was noisy."
    )


def incident(world: World) -> None:
    mystery: Mystery = world.facts["mystery"]
    hero: Entity = world.facts["hero"]
    world.say(
        f"Behold, {world.setting.place} had {mystery.stain} on the floor, and the smell of {mystery.spill} was in the air."
    )
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.facts["scene_clue"] = mystery.clue


def detect(world: World) -> None:
    mystery: Mystery = world.facts["mystery"]
    hero: Entity = world.facts["hero"]
    ally: Entity = world.facts["ally"]
    hero.memes["focus"] = hero.memes.get("focus", 0) + 1
    world.say(
        f"{hero.id} followed the red drips like a trail and asked {ally.id} careful questions."
    )
    world.say(
        f"The clues pointed to {mystery.cause}, not to a mean trick."
    )
    world.facts["truth"] = mystery.cause


def misunderstanding(world: World) -> None:
    hero: Entity = world.facts["hero"]
    ally: Entity = world.facts["ally"]
    hero.memes["irritation"] = hero.memes.get("irritation", 0) + 1
    ally.memes["shame"] = ally.memes.get("shame", 0) + 1
    world.say(
        f"{hero.id} frowned at first, because it looked as if {ally.id} had caused the mess on purpose."
    )
    world.say(
        f"But {ally.id} lowered {ally.pronoun('possessive')} eyes and explained that {ally.pronoun()} had only tried to help."
    )


def reconcile(world: World) -> None:
    hero: Entity = world.facts["hero"]
    ally: Entity = world.facts["ally"]
    hero.memes["understanding"] = hero.memes.get("understanding", 0) + 1
    ally.memes["relief"] = ally.memes.get("relief", 0) + 1
    hero.memes["irritation"] = 0
    world.say(
        f"{hero.id} took a breath and said sorry for jumping to conclusions."
    )
    world.say(
        f"{ally.id} smiled, and the two of them made up before the work began."
    )


def solve_problem(world: World) -> None:
    mystery: Mystery = world.facts["mystery"]
    hero: Entity = world.facts["hero"]
    ally: Entity = world.facts["ally"]
    world.say(
        f"Together they got paper towels, wiped the sticky red marks, and scrubbed until the floor shone again."
    )
    world.say(
        f"They found the broken cup, set the snacks straight, and learned a kinder way to ask for help."
    )
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    ally.memes["helpfulness"] = ally.memes.get("helpfulness", 0) + 1
    world.facts["resolved"] = True
    world.facts["solution"] = mystery.method


def closing_image(world: World) -> None:
    hero: Entity = world.facts["hero"]
    ally: Entity = world.facts["ally"]
    world.say(
        f"In the end, {hero.id} was still a detective, but now {hero.id} knew that good clues and kind words could solve a problem together."
    )
    world.say(
        f"{ally.id} brought the cookies over, and the room felt calm and friendly again."
    )


def tell_story(world: World) -> World:
    introduce(world)
    world.para()
    incident(world)
    detect(world)
    misunderstanding(world)
    world.para()
    reconcile(world)
    solve_problem(world)
    closing_image(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]
    ally: Entity = world.facts["ally"]
    mystery: Mystery = world.facts["mystery"]
    return [
        f'Write a gentle detective story for a young child that includes the word "behold" and a {mystery.spill} mess.',
        f"Tell a story where {hero.id} thinks {ally.id} caused a {mystery.spill} problem, then discovers the real clue and makes up.",
        f"Write a short problem-solving story about a child detective, a red spill of koolaid, and reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    ally: Entity = world.facts["ally"]
    mystery: Mystery = world.facts["mystery"]
    return [
        QAItem(
            question=f"What did {hero.id} notice in {world.setting.place}?",
            answer=f"{hero.id} noticed {mystery.stain} and the smell of {mystery.spill} in {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {hero.id} think there was a problem at first?",
            answer=f"At first, {hero.id} thought {ally.id} had caused the mess on purpose, because the clues were confusing.",
        ),
        QAItem(
            question=f"How did the story end after they solved the problem?",
            answer=f"They cleaned the mess, understood the real cause, and made up before the snacks were served.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is koolaid?",
            answer="Koolaid is a sweet drink that can spill and leave colorful stains.",
        ),
        QAItem(
            question="What does behold mean?",
            answer="Behold is a word that means look carefully or notice something important.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people make peace after a disagreement or misunderstanding.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means figuring out what is wrong and then finding a good way to fix it.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(kitchen).
setting(hallway).
setting(classroom).

mystery(spill).
mystery(tablecloth).

has_koolaid(spill).
has_koolaid(tablecloth).

clue(spill, red_drips).
clue(tablecloth, wet_corners).

causes(spill, tipped_cup).
causes(tablecloth, elbow_knock).

solves(spill, cleaning_floor).
solves(tablecloth, washing_cloth).

compatible(S, M) :- setting(S), mystery(M), has_koolaid(M), clue(M, _), causes(M, _), solves(M, _).
#show compatible/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("has_koolaid", mid))
        lines.append(asp.fact("clue", mid, m.clue))
        lines.append(asp.fact("causes", mid, m.cause))
        lines.append(asp.fact("solves", mid, m.method))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_combos() -> list[tuple[str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    out = []
    for s in SETTINGS:
        for m in MYSTERIES:
            out.append((s, m))
    return out


def explain_rejection(setting: str, mystery: str) -> str:
    return f"(No story: the setting {setting!r} and mystery {mystery!r} do not make a coherent detective scene.)"


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def valid_name_pool(gender: str) -> list[str]:
    return NAMES[gender]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    if setting not in SETTINGS or mystery not in MYSTERIES:
        raise StoryError("(No valid combination matches the given options.)")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(valid_name_pool(gender))
    ally = args.ally or rng.choice(ROLES)
    role = args.role or "detective"
    return StoryParams(setting=setting, mystery=mystery, name=name, gender=gender, ally=ally, role=role)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(setup_world(params))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


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
    lines.append("== World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world: koolaid, clues, reconciliation, and problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--ally", choices=ROLES)
    ap.add_argument("--role")
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


CURATED = [
    StoryParams(setting="kitchen", mystery="spill", name="Mina", gender="girl", ally="brother", role="detective"),
    StoryParams(setting="classroom", mystery="tablecloth", name="Leo", gender="boy", ally="friend", role="detective"),
]


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
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_combos()
        print(f"{len(combos)} compatible setting/mystery combos:\n")
        for s, m in combos:
            print(f"  {s:10} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mystery} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
