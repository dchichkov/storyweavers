#!/usr/bin/env python3
"""
A standalone storyworld script for a humble, kind, brave rhyming tale.

The tiny domain:
- A small character notices a problem near a simple setting.
- They feel humble, choose kindness, and show bravery.
- They help another creature or friend through a little challenge.
- The ending proves what changed in the world: a safe home, a calm heart,
  and a kind deed remembered.

The prose is intentionally rhythmic and child-facing, with state-driven beats.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "father", "dad", "man", "fox", "owl"}
        female = {"girl", "mother", "mom", "woman", "mouse"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    afford: str
    detail: str


@dataclass
class Spark:
    id: str
    name: str
    tiny_problem: str
    brave_action: str
    humble_step: str
    ending_line: str
    risk_meter: str
    helper_kind: str


@dataclass
class StoryParams:
    setting: str
    spark: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}

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
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "garden": Setting(
        place="the garden",
        afford="follow a small glow",
        detail="The garden was soft with grass, and moonlight made the petals shine.",
    ),
    "meadow": Setting(
        place="the meadow",
        afford="cross the tall grass",
        detail="The meadow was wide and green, with daisies bobbing in the breeze.",
    ),
    "brook": Setting(
        place="the brook",
        afford="cross the little stones",
        detail="The brook went splash and shimmer, and the stones were smooth and round.",
    ),
}

SPARKS = {
    "lantern": Spark(
        id="lantern",
        name="lantern",
        tiny_problem="the lantern had gone dim",
        brave_action="carry the lantern through the dark",
        humble_step="ask for help with a small bow",
        ending_line="The lantern glowed again, warm and bright, and the path felt safe all night.",
        risk_meter="dim",
        helper_kind="friend",
    ),
    "lost_bird": Spark(
        id="lost_bird",
        name="lost bird",
        tiny_problem="a little bird had lost its nest",
        brave_action="climb the branch and look around",
        humble_step="listen before choosing the way",
        ending_line="The bird found its nest at last, and the treetop cheered in the breeze.",
        risk_meter="lost",
        helper_kind="friend",
    ),
    "shy_mouse": Spark(
        id="shy_mouse",
        name="shy mouse",
        tiny_problem="a shy mouse could not cross the creek",
        brave_action="step over the stones one by one",
        humble_step="offer a paw and speak soft and low",
        ending_line="The mouse crossed with a tiny smile, and the creek sang on with cheer.",
        risk_meter="stuck",
        helper_kind="friend",
    ),
}

HEROES = [
    ("pippin", "mouse"),
    ("toby", "fox"),
    ("mira", "girl"),
    ("elliot", "boy"),
]

HELPERS = [
    ("bunny", "rabbit"),
    ("nora", "girl"),
    ("piper", "bird"),
    ("fenn", "fox"),
]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    return [(s, sp) for s in SETTINGS for sp in SPARKS]


def explain_rejection(setting: str, spark: str) -> str:
    return f"(No story: the setting {setting!r} and spark {spark!r} do not fit a small brave kindness tale.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(S) :- place(S).
spark(K) :- tiny_problem(K,_).
valid(S,K) :- setting(S), spark(K).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("place", sid))
    for kid in SPARKS:
        lines.append(asp.fact("tiny_problem", kid, kid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if py == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - clingo_set:
        print("  only in python:", sorted(py - clingo_set))
    if clingo_set - py:
        print("  only in clingo:", sorted(clingo_set - py))
    return 1


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------

def rhyme(a: str, b: str) -> str:
    return f"{a} {b}"


def build_line(a: str, b: str, c: str) -> str:
    return f"{a} {b}, {c}."


def do_kindness(world: World, hero: Entity, helper: Entity, spark: Spark) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    hero.memes["humble"] = hero.memes.get("humble", 0.0) + 1
    helper.memes["trust"] = helper.memes.get("trust", 0.0) + 1
    world.say(
        f"{hero.id} gave a humble grin and a gentle spin, "
        f"for kindness is bright and kindness wins."
    )
    world.say(
        f"{helper.id} came near with a helpful cheer, "
        f"and stood beside {hero.pronoun('object')} without a sneer."
    )


def do_bravery(world: World, hero: Entity, spark: Spark) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    hero.meters["risk"] = hero.meters.get("risk", 0.0) + 1
    world.say(
        f"{hero.id} felt a flutter, then a steady stare, "
        f"and chose brave feet to go right there."
    )
    world.say(
        f"{hero.id} said, \"I can try, though the way looks high; "
        f"I'll step with care and reach the sky.\""
    )


def resolve_spark(world: World, hero: Entity, helper: Entity, spark: Spark) -> None:
    hero.meters[spark.risk_meter] = max(0.0, hero.meters.get(spark.risk_meter, 0.0) - 1.0)
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1
    world.say(
        f"Together they worked with steady part, "
        f"and fixed the little trouble with an open heart."
    )
    world.say(spark.ending_line)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    spark = SPARKS[params.spark]
    world = World(setting)

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))

    hero.memes["humble"] = 1.0
    hero.memes["kindness"] = 0.0
    hero.memes["bravery"] = 0.0

    world.say(
        f"In {setting.place}, by soft green land, {hero.id} walked with a tiny plan."
    )
    world.say(
        f"{hero.id} was humble, small, and kind; {hero.id} kept a warm and wondering mind."
    )
    world.say(
        f"Then came {spark.name}: {spark.tiny_problem}, and that was not fine."
    )

    world.para()
    world.say(setting.detail)
    world.say(
        f"{hero.id} saw the trouble and did not flee; "
        f"{hero.id} chose bravery as bold as could be."
    )
    world.say(f"{hero.id} {spark.humble_step}, and asked {helper.id} to agree.")

    world.para()
    do_kindness(world, hero, helper, spark)
    do_bravery(world, hero, spark)
    resolve_spark(world, hero, helper, spark)

    world.facts.update(
        hero=hero,
        helper=helper,
        spark=spark,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    spark = f["spark"]
    setting = f["setting"]
    return [
        f'Write a short rhyming story for a child about {hero.id}, '
        f'who shows humble kindness and bravery in {setting.place}.',
        f'Tell a gentle rhyming tale where {hero.id} helps {spark.name} '
        f'and asks {helper.id} for help with a humble heart.',
        f'Write a bright, simple story with rhyme, kindness, and bravery, '
        f'ending with a happy change in {setting.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    spark: Spark = f["spark"]
    setting: Setting = f["setting"]

    return [
        QAItem(
            question=f"Who was the story about in {setting.place}?",
            answer=f"The story was about {hero.id}, who stayed humble, kind, and brave in {setting.place}.",
        ),
        QAItem(
            question=f"What problem did {spark.name} have?",
            answer=f"{spark.tiny_problem.capitalize()}. {hero.id} noticed it and chose to help.",
        ),
        QAItem(
            question=f"Who helped {hero.id}?",
            answer=f"{helper.id} helped {hero.id}, and the two worked together with gentle care.",
        ),
        QAItem(
            question=f"What brave thing did {hero.id} do?",
            answer=f"{hero.id} chose to {spark.brave_action}, even though it felt a little scary at first.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=spark.ending_line,
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What does humble mean?",
        answer="Humble means not showing off and being gentle, thankful, and modest.",
    ),
    QAItem(
        question="What is kindness?",
        answer="Kindness means being caring and helpful to others.",
    ),
    QAItem(
        question="What is bravery?",
        answer="Bravery means doing the right thing even when you feel afraid.",
    ),
    QAItem(
        question="Why do helpers matter in a story?",
        answer="Helpers matter because they can share the work, offer comfort, and make a hard thing feel easier.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.spark and (args.setting, args.spark) not in valid_combos():
        raise StoryError(explain_rejection(args.setting, args.spark))
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.spark:
        combos = [c for c in combos if c[1] == args.spark]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, spark = rng.choice(sorted(combos))
    hero_name, hero_type = rng.choice(HEROES)
    helper_name, helper_type = rng.choice(HELPERS)
    if helper_name == hero_name:
        helper_name, helper_type = "luma", "bird"
    return StoryParams(
        setting=setting,
        spark=spark,
        hero_name=args.name or hero_name,
        hero_type=args.hero_type or hero_type,
        helper_name=args.helper_name or helper_name,
        helper_type=args.helper_type or helper_type,
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="garden", spark="lantern", hero_name="pippin", hero_type="mouse", helper_name="bunny", helper_type="rabbit"),
    StoryParams(setting="meadow", spark="lost_bird", hero_name="mira", hero_type="girl", helper_name="piper", helper_type="bird"),
    StoryParams(setting="brook", spark="shy_mouse", hero_name="elliot", hero_type="boy", helper_name="nora", helper_type="girl"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Humble kindness bravery rhyming storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--spark", choices=SPARKS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["mouse", "fox", "girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["rabbit", "fox", "bird", "girl", "boy"])
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


def asp_verify_wrapper() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify_wrapper())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
