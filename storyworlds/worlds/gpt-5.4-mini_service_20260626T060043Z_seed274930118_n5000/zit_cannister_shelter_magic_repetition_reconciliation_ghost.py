#!/usr/bin/env python3
"""
A small ghost-story world about a zit, a cannister, and a shelter.

The seed tale behind this world:
A little ghost named Pip wakes up with a stubborn zit glowing on its cheek.
It worries the other ghosts will laugh. In the shelter, Pip finds a dusty
cannister that hums with old moon-magic. The magic only works if Pip repeats
a kind phrase three times. When Pip does, the shelter stops creaking, the zit
shrinks, and Pip learns that being seen kindly is better than hiding.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "ghost":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the shelter"
    indoors: bool = True
    haunted: bool = True


@dataclass
class MagicThing:
    id: str
    label: str
    phrase: str
    effect: str
    repeats: int
    requires_kindness: bool = True


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    companion_name: str
    companion_type: str
    setting: str
    magic: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
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
        other = World(self.setting)
        other.entities = {
            k: Entity(**{**vars(v), "meters": dict(v.meters), "memes": dict(v.memes), "traits": list(v.traits)})
            for k, v in self.entities.items()
        }
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        return other


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "shelter": Setting(place="the shelter", indoors=True, haunted=True),
}

MAGICS = {
    "moon_can": MagicThing(
        id="moon_can",
        label="moon-lit cannister",
        phrase="an old cannister with a silver moon on its side",
        effect="the ache faded",
        repeats=3,
        requires_kindness=True,
    ),
    "lantern_can": MagicThing(
        id="lantern_can",
        label="lantern cannister",
        phrase="a dented cannister that glowed like a tiny lantern",
        effect="the room stopped shivering",
        repeats=2,
        requires_kindness=True,
    ),
}

GHOST_NAMES = ["Pip", "Moss", "Boo", "Nell", "Wisp", "Ivy"]
HUMAN_NAMES = ["Mina", "Owen", "June", "Theo", "Lena", "Finn"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is reasonable when it has a shelter, a magic cannister, and a ghost
% with a zit that can be soothed through repetition and reconciliation.
can_story(S, M) :- setting(S), magic(M), shelter(S), uses_repetition(M), has_kindness(M).
valid_story(S, M) :- can_story(S, M), heals_zit(M), mends_fear(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("shelter", sid))
    for mid, m in MAGICS.items():
        lines.append(asp.fact("magic", mid))
        lines.append(asp.fact("uses_repetition", mid))
        if m.requires_kindness:
            lines.append(asp.fact("has_kindness", mid))
        if m.effect:
            lines.append(asp.fact("mends_fear", mid))
        lines.append(asp.fact("heals_zit", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p.setting, p.magic) for p in valid_combos()}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} valid stories.")
        return 0
    print("MISMATCH between ASP and Python:")
    print(" only python:", sorted(py - cl))
    print(" only ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def valid_combos() -> list[StoryParams]:
    out: list[StoryParams] = []
    for setting in SETTINGS:
        for magic in MAGICS:
            out.append(StoryParams(
                hero_name="Pip",
                hero_type="ghost",
                companion_name="Mina",
                companion_type="child",
                setting=setting,
                magic=magic,
            ))
    return out


def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.magic not in MAGICS:
        raise StoryError(f"Unknown magic object: {params.magic}")

    setting = SETTINGS[params.setting]
    magic = MAGICS[params.magic]
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="ghost",
        type=params.hero_type,
        traits=["lonely", "shy"],
        meters={"zit": 1.0, "fear": 1.0},
        memes={"shame": 1.0, "hope": 0.0, "calm": 0.0, "reconciled": 0.0},
    ))
    companion = world.add(Entity(
        id=params.companion_name,
        kind="person",
        type=params.companion_type,
        traits=["kind", "patient"],
        meters={},
        memes={"kindness": 1.0},
    ))
    can = world.add(Entity(
        id=magic.id,
        kind="thing",
        type="cannister",
        label="cannister",
        phrase=magic.phrase,
        owner=hero.id,
        caretaker=companion.id,
        meters={"magic": 1.0},
        memes={"hum": 1.0},
    ))

    world.facts.update(hero=hero, companion=companion, can=can, magic=magic, setting=setting)
    return world


def _narrate_setup(world: World) -> None:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    can = world.facts["can"]
    world.say(
        f"Inside the shelter, {hero.id} drifted from corner to corner, trying not to let anyone see the zit on {hero.pronoun('possessive')} cheek."
    )
    world.say(
        f"{companion.id} found {can.phrase} tucked under a blanket, and the little cannister gave off a soft, moon-pale hum."
    )


def _activate_magic(world: World) -> None:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    magic: MagicThing = world.facts["magic"]
    world.para()
    world.say(
        f"{companion.id} said, 'Sometimes magic only answers when you repeat the right words.'"
    )
    world.say(
        f"So {hero.id} whispered, '{hero.id} can be brave,' then said it again, and again."
    )
    hero.memes["hope"] += 1.0
    hero.memes["calm"] += 1.0
    hero.meters["zit"] = 0.0
    hero.memes["shame"] = 0.0
    hero.memes["reconciled"] = 1.0
    companion.memes["kindness"] += 0.5
    world.facts["repetitions"] = magic.repeats
    world.facts["magic_effect"] = magic.effect


def _resolve(world: World) -> None:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    world.para()
    world.say(
        f"On the third repeat, the cannister warmed like a tiny sunrise, and {hero.id}'s zit shrank away as if it had never wanted to stay."
    )
    world.say(
        f"{hero.id} stopped hiding and floated close to {companion.id}. They did not need to be perfect to be together; they only needed to be kind."
    )
    world.say(
        f"The shelter grew quiet and safe, and the old cannister kept glowing softly beside them."
    )


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    _narrate_setup(world)
    _activate_magic(world)
    _resolve(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    can = world.facts["can"]
    return [
        "Write a gentle ghost story about a child-friendly ghost, a glowing cannister, and a problem that gets better after repeating kind words.",
        f"Tell a spooky-but-sweet story in a shelter where {hero.id} has a zit and discovers magic in {can.label}.",
        "Create a short story that uses repetition, magic, and reconciliation, ending with a calm shelter and a happier ghost.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    comp = world.facts["companion"]
    can = world.facts["can"]
    magic: MagicThing = world.facts["magic"]
    return [
        QAItem(
            question=f"What worried {hero.id} at the start of the story?",
            answer=f"{hero.id} worried about the zit on {hero.pronoun('possessive')} cheek and tried to hide it in the shelter.",
        ),
        QAItem(
            question=f"What did {comp.id} find in the shelter?",
            answer=f"{comp.id} found {can.phrase}, a magic cannister that needed repeated kind words before it would work.",
        ),
        QAItem(
            question="What had to happen before the magic worked?",
            answer=f"The kind phrase had to be repeated {magic.repeats} times, and the speaking had to come from kindness instead of fear.",
        ),
        QAItem(
            question=f"What changed after the third repeat?",
            answer=f"The cannister warmed up, the zit shrank away, and {hero.id} stopped hiding and felt reconciled.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cannister?",
            answer="A cannister is a container, often made of metal, that can hold things safely inside it.",
        ),
        QAItem(
            question="What is a shelter?",
            answer="A shelter is a place that keeps someone safe from bad weather, danger, or fear.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing or saying the same thing more than once. In stories, repeating words can help magic work.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means two sides stop fighting or feeling apart and come back together kindly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== story qa =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for ent in world.entities.values():
        lines.append(f"{ent.id}: kind={ent.kind} type={ent.type} meters={ent.meters} memes={ent.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost story world of magic, repetition, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--magic", choices=MAGICS.keys())
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
    setting = args.setting or rng.choice(list(SETTINGS.keys()))
    magic = args.magic or rng.choice(list(MAGICS.keys()))
    if setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {setting}")
    if magic not in MAGICS:
        raise StoryError(f"Unknown magic: {magic}")
    return StoryParams(
        hero_name="Pip",
        hero_type="ghost",
        companion_name=rng.choice(HUMAN_NAMES),
        companion_type="child",
        setting=setting,
        magic=magic,
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible story combos:")
        for setting, magic in combos:
            print(f"  {setting} {magic}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in valid_combos()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        if len(samples) > 1 and not args.all:
            print(f"### variant {idx + 1}")
        elif args.all:
            print(f"### {sample.params.hero_name} in {sample.params.setting} with {sample.params.magic}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
