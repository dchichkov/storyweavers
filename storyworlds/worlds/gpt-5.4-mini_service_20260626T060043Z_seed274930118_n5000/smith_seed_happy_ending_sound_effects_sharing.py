#!/usr/bin/env python3
"""
storyworlds/worlds/smith_seed_happy_ending_sound_effects_sharing.py
====================================================================

A tiny fable-like story world about a smith, a seed, sound effects, and sharing.

Seed tale inspiration:
---
A smith finds a single seed on the forge floor. The smith wants to keep it safe,
but a small friend asks if it can be shared. The smith listens, plants the seed
with care, and the seed grows into something lovely for everyone.

This world turns that premise into a small simulation:
- the smith can keep, carry, plant, or share the seed
- sharing lowers greed and raises warmth and trust
- planting changes the seed into a sprout and then into a bright ending image
- sound effects ("clang", "ting", "tap", "whoosh") are narrated from state changes
- the story always ends with the seed shared and the outcome made visible

Style target:
- fable-like
- child-facing
- concrete
- with a happy ending and a small moral turn
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

SOUND_EFFECTS = {
    "forge": "clang",
    "small": "ting",
    "plant": "tap",
    "grow": "whoosh",
    "share": "softly",
}

REGIONS = {"hands", "heart", "ground"}


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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "smithess"}
        male = {"boy", "man", "father", "smith"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    kind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class SeedKind:
    id: str
    label: str
    phrase: str
    grow_word: str
    sound: str
    ending: str
    requires: set[str] = field(default_factory=set)


@dataclass
class Companion:
    id: str
    label: str
    type: str
    trait: str
    request: str
    reason: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_stir(world: World) -> list[str]:
    out: list[str] = []
    smiths = [e for e in world.entities.values() if e.kind == "character" and e.type in {"smith", "smithess"}]
    for smith in smiths:
        if smith.meters["forge"] < THRESHOLD:
            continue
        sig = ("stir", smith.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        smith.memes["focus"] += 1
        out.append(f"{SOUND_EFFECTS['forge'].capitalize()}! {smith.label or smith.id} kept the fire bright.")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    seed = world.entities.get("seed")
    companion = world.entities.get("companion")
    smith = world.entities.get("smith")
    if not seed or not companion or not smith:
        return out
    if seed.meters["shared"] < THRESHOLD:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    smith.memes["warmth"] += 1
    companion.memes["trust"] += 1
    seed.memes["belonging"] += 1
    out.append(f"{SOUND_EFFECTS['share'].capitalize()} the smith passed the seed to the small friend.")
    return out


def _r_plant(world: World) -> list[str]:
    out: list[str] = []
    seed = world.entities.get("seed")
    smith = world.entities.get("smith")
    if not seed or not smith:
        return out
    if seed.meters["planted"] < THRESHOLD:
        return out
    sig = ("plant",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    seed.meters["sprout"] += 1
    seed.memes["hope"] += 1
    out.append(f"{SOUND_EFFECTS['plant'].capitalize()}! The seed settled into the earth.")
    return out


def _r_grow(world: World) -> list[str]:
    out: list[str] = []
    seed = world.entities.get("seed")
    if not seed:
        return out
    if seed.meters["sprout"] < THRESHOLD or seed.meters["grown"] >= THRESHOLD:
        return out
    sig = ("grow",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    seed.meters["grown"] += 1
    seed.memes["joy"] += 1
    out.append(f"{SOUND_EFFECTS['grow'].capitalize()}! Up came {seed.label}, small at first and then bright.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("stir", "forge", _r_stir),
    Rule("share", "social", _r_share),
    Rule("plant", "physical", _r_plant),
    Rule("grow", "physical", _r_grow),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "forge": Setting(place="the forge", kind="forge", affords={"hold", "share"}),
    "garden": Setting(place="the garden", kind="garden", affords={"plant", "share"}),
    "village_green": Setting(place="the village green", kind="green", affords={"plant", "share"}),
}

SEEDS = {
    "sun": SeedKind(
        id="sun",
        label="sunseed",
        phrase="a bright sunseed",
        grow_word="sunny",
        sound="ting",
        ending="a warm patch of flowers that faced the morning light",
        requires={"garden", "green"},
    ),
    "oak": SeedKind(
        id="oak",
        label="oakseed",
        phrase="a sturdy oakseed",
        grow_word="strong",
        sound="tap",
        ending="a little oak sapling with kind, leafy shade",
        requires={"garden", "green"},
    ),
    "song": SeedKind(
        id="song",
        label="songseed",
        phrase="a silver songseed",
        grow_word="singing",
        sound="clang",
        ending="a tree whose leaves chimed like tiny bells",
        requires={"forge", "garden", "green"},
    ),
}

COMPANIONS = {
    "mouse": Companion(
        id="mouse",
        label="the mouse",
        type="mouse",
        trait="small",
        request="share it with the nest",
        reason="the nest needed one bright thing to cheer the little ones",
    ),
    "child": Companion(
        id="child",
        label="the child",
        type="child",
        trait="curious",
        request="plant it in a safe place",
        reason="the town needed a kinder, greener corner",
    ),
}

SMITH_NAMES = ["Ivo", "Mara", "Nell", "Tomas", "Sera", "Bram"]
TRAITS = ["kind", "patient", "proud", "careful", "thoughtful", "cheerful"]


@dataclass
class StoryParams:
    setting: str
    seed_kind: str
    companion: str
    name: str
    trait: str
    seed: Optional[int] = None


def story_is_reasonable(setting: str, seed_kind: str) -> bool:
    return setting in SETTINGS and seed_kind in SEEDS and SETTINGS[setting].kind in SEEDS[seed_kind].requires


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.seed_kind and not story_is_reasonable(args.setting, args.seed_kind):
        raise StoryError("That seed would not reasonably grow in that setting.")
    options = []
    for s in SETTINGS:
        for sk in SEEDS:
            if not story_is_reasonable(s, sk):
                continue
            if args.setting and s != args.setting:
                continue
            if args.seed_kind and sk != args.seed_kind:
                continue
            options.append((s, sk))
    if not options:
        raise StoryError("No valid story matches the given options.")
    setting, seed_kind = rng.choice(sorted(options))
    comp = args.companion or rng.choice(list(COMPANIONS))
    name = args.name or rng.choice(SMITH_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, seed_kind=seed_kind, companion=comp, name=name, trait=trait)


def introduce(world: World, smith: Entity, seed: Entity, companion: Entity, sk: SeedKind) -> None:
    world.say(
        f"{smith.id} was a {smith.traits[0]} smith who worked with a steady hand and a listening ear."
    )
    world.say(
        f"One day {smith.pronoun('subject')} found {sk.phrase} near the anvil and heard a tiny {sk.sound}: "
        f"the seed seemed to be waiting for a friend."
    )
    world.say(
        f"{companion.label.capitalize()} came close and asked to {companion.memes['ask_text']}. "
        f"It was a gentle request, because {companion.reason}."
    )


def tension(world: World, smith: Entity, seed: Entity, companion: Entity, sk: SeedKind) -> None:
    smith.memes["greed"] += 1
    seed.meters["held"] += 1
    world.say(
        f"{smith.id} kept the seed in {smith.pronoun('possessive')} palm. {SOUND_EFFECTS['small'].capitalize()}! "
        f"It felt important, and {smith.pronoun('subject')} was not yet ready to let it go."
    )
    world.say(
        f"But {companion.label} pointed to the empty earth outside the door and said, "
        f'"Will you share it?"'
    )


def decide_share(world: World, smith: Entity, seed: Entity, companion: Entity) -> None:
    smith.memes["greed"] = max(0.0, smith.memes["greed"] - 1)
    seed.meters["shared"] += 1
    world.say(
        f"{smith.id} thought of the town, the child, and the little nest. Then {smith.pronoun('subject')} smiled."
    )
    world.say(
        f"{smith.id} opened {smith.pronoun('possessive')} hand and shared the seed."
    )
    propagate(world, narrate=True)


def plant_and_end(world: World, smith: Entity, seed: Entity, companion: Entity, sk: SeedKind) -> None:
    seed.meters["planted"] += 1
    propagate(world, narrate=True)
    if seed.meters["grown"] >= THRESHOLD:
        world.say(
            f"Together they watched the new growth, and the little place became {sk.ending}."
        )
        world.say(
            f"The smith learned that a seed kept alone stays one seed, but a seed shared can become a gift."
        )


def tell(setting: Setting, sk: SeedKind, comp: Companion, hero_name: str = "Mara", trait: str = "kind") -> World:
    world = World(setting)
    smith = world.add(Entity(id=hero_name, kind="character", type="smith", traits=[trait, "steady"]))
    companion = world.add(Entity(id="companion", kind="character", type=comp.type, label=comp.label, traits=[comp.trait]))
    seed = world.add(Entity(id="seed", kind="thing", type="seed", label=sk.label, phrase=sk.phrase, caretaker=smith.id))
    smith.meters["forge"] += 1
    companion.memes["ask_text"] = 0  # stored below as plain text in narrative helper
    world.facts["setting"] = setting
    world.facts["seed_kind"] = sk
    world.facts["companion"] = comp
    world.facts["smith"] = smith
    world.facts["seed"] = seed
    world.facts["companion_obj"] = companion

    introduce_text = [
        f"{smith.id} was a {trait} smith who worked beside the fire.",
        f"One day {smith.pronoun('subject')} found {sk.phrase} by the anvil, and it gave off a tiny {sk.sound}.",
        f"{comp.label.capitalize()} asked, \"Will you share it with me?\"",
    ]
    world.say(introduce_text[0])
    world.say(introduce_text[1])
    world.say(introduce_text[2])

    world.para()
    tension(world, smith, seed, companion, sk)

    world.para()
    decide_share(world, smith, seed, companion)
    plant_and_end(world, smith, seed, companion, sk)

    world.facts.update(shared=seed.meters["shared"] >= THRESHOLD, grown=seed.meters["grown"] >= THRESHOLD)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short fable about a {f['smith'].type} who finds {f['seed_kind'].phrase} and learns to share it.",
        f"Tell a happy-ending story with sound effects about {f['smith'].id}, {f['companion'].label}, and a seed.",
        f"Write a child-friendly fable where a smith keeps a seed, hears a request, and ends by sharing it.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    smith: Entity = f["smith"]
    seed: Entity = f["seed"]
    sk: SeedKind = f["seed_kind"]
    comp: Companion = f["companion"]
    return [
        QAItem(
            question=f"What did {smith.id} find by the anvil?",
            answer=f"{smith.id} found {sk.phrase} by the anvil.",
        ),
        QAItem(
            question=f"What did {comp.label} ask {smith.id} to do?",
            answer=f"{comp.label.capitalize()} asked {smith.id} to share the seed.",
        ),
        QAItem(
            question=f"How did the story end after the seed was shared?",
            answer=f"The seed was planted, it grew, and the ending became {sk.ending}.",
        ),
        QAItem(
            question=f"What sound did the seed make when {smith.id} found it?",
            answer=f"It made a tiny {sk.sound} sound.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "seed": [
        (
            "What is a seed?",
            "A seed is a tiny part of a plant that can grow into a new plant when it gets water, soil, and care.",
        )
    ],
    "sharing": [
        (
            "What does sharing mean?",
            "Sharing means giving some of what you have so someone else can enjoy it too.",
        )
    ],
    "forge": [
        (
            "What does a smith do at a forge?",
            "A smith heats and shapes metal at a forge, often using fire, an anvil, and a hammer.",
        )
    ],
    "sound": [
        (
            "Why do stories use sound effects?",
            "Sound effects help readers imagine what a scene feels and sounds like, like a clang or a whoosh.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for group in WORLD_KNOWLEDGE.values() for q, a in group]


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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s in SETTINGS:
        for sk in SEEDS:
            if story_is_reasonable(s, sk):
                combos.append((s, sk))
    return combos


ASP_RULES = r"""
valid(S, K) :- setting(S), seed_kind(K), setting_kind(S, KS), requires(K, KS).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("setting_kind", sid, s.kind))
    for kid, k in SEEDS.items():
        lines.append(asp.fact("seed_kind", kid))
        for req in sorted(k.requires):
            lines.append(asp.fact("requires", kid, req))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small fable-like story world about a smith, a seed, sound effects, and sharing."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--seed-kind", choices=SEEDS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        SEEDS[params.seed_kind],
        COMPANIONS[params.companion],
        hero_name=params.name,
        trait=params.trait,
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


CURATED = [
    StoryParams(setting="garden", seed_kind="song", companion="mouse", name="Mara", trait="kind"),
    StoryParams(setting="village_green", seed_kind="oak", companion="child", name="Bram", trait="thoughtful"),
    StoryParams(setting="garden", seed_kind="sun", companion="child", name="Nell", trait="cheerful"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.seed_kind and not story_is_reasonable(args.setting, args.seed_kind):
        raise StoryError("That seed would not reasonably fit that setting.")
    combos = [
        (s, sk)
        for s, sk in valid_combos()
        if (args.setting is None or s == args.setting)
        and (args.seed_kind is None or sk == args.seed_kind)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, seed_kind = rng.choice(sorted(combos))
    companion = args.companion or rng.choice(list(COMPANIONS))
    name = args.name or rng.choice(SMITH_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, seed_kind=seed_kind, companion=companion, name=name, trait=trait)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible setting/seed combos:\n")
        for setting, seed_kind in combos:
            print(f"  {setting:13} {seed_kind}")
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
            header = f"### {p.name}: {p.seed_kind} at {p.setting} (companion: {p.companion})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
