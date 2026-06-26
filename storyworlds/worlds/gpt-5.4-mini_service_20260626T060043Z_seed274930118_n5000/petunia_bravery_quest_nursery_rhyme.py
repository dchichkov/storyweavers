#!/usr/bin/env python3
"""
storyworlds/worlds/petunia_bravery_quest_nursery_rhyme.py
==========================================================

A small, classical story world in a nursery-rhyme tone.

Premise:
- Petunia is a tiny flower-child with a brave heart that can still tremble.
- She must take a quest across the garden to bring back one gentle thing.
- The world keeps track of physical position and emotional courage.
- The story changes based on the quest, the place, and the helper.

This world is intentionally compact: fewer, stronger variations, with each
sample driven by a short simulation rather than a template swap.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core world objects
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "flower-child"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    mood: str
    trail: list[str] = field(default_factory=list)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    risk: str
    turn: str
    ending: str
    path: list[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Reward:
    id: str
    label: str
    phrase: str
    color: str
    kind: str
    safe_if: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.lines = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "nursery_garden": Setting(place="the nursery garden", mood="soft and sunny",
                              trail=["gate", "ladder", "pond", "arch"]),
    "moon_path": Setting(place="the moonlit path", mood="silver and quiet",
                         trail=["gate", "stones", "bushes", "moonbeam"]),
    "orchard_edge": Setting(place="the orchard edge", mood="bright and breezy",
                            trail=["gate", "apples", "fence", "hive"]),
}

QUESTS = {
    "dew_drop": Quest(
        id="dew_drop",
        verb="bring back the dew drop",
        gerund="bringing back the dew drop",
        risk="the dew drop might shake and spill",
        turn="a little snail showed the safest stepping stones",
        ending="the dew drop still glittered in Petunia's leaf",
        path=["gate", "stones", "pond"],
        tags={"water", "care"},
    ),
    "moon_bell": Quest(
        id="moon_bell",
        verb="find the moon bell",
        gerund="finding the moon bell",
        risk="the dark path felt too wide and windy",
        turn="a firefly lit the way with a tiny wink of gold",
        ending="the moon bell rang like a pebble song",
        path=["gate", "bushes", "moonbeam"],
        tags={"night", "light"},
    ),
    "honey_note": Quest(
        id="honey_note",
        verb="deliver the honey note",
        gerund="delivering the honey note",
        risk="the note might smudge in the breeze",
        turn="a bee tucked it under a safe petal",
        ending="the honey note arrived sweet and neat",
        path=["gate", "ladder", "hive"],
        tags={"bee", "message"},
    ),
}

REWARDS = {
    "dew_drop": Reward(
        id="dew_drop",
        label="dew drop",
        phrase="a clear dew drop",
        color="silver",
        kind="water",
        safe_if={"snail", "stones"},
    ),
    "moon_bell": Reward(
        id="moon_bell",
        label="moon bell",
        phrase="a small bell of moonlight",
        color="pale gold",
        kind="sound",
        safe_if={"firefly", "moonbeam"},
    ),
    "honey_note": Reward(
        id="honey_note",
        label="honey note",
        phrase="a tiny honey note",
        color="amber",
        kind="message",
        safe_if={"bee", "petal"},
    ),
}

HELPERS = {
    "snail": {"label": "a snail", "kind": "snail", "meter": "slowness"},
    "firefly": {"label": "a firefly", "kind": "firefly", "meter": "glow"},
    "bee": {"label": "a bee", "kind": "bee", "meter": "hum"},
}

GIRL_NAMES = ["Petunia", "Mina", "Lila", "Tessa", "Nora", "Daisy"]
TRAITS = ["tiny", "gentle", "curious", "soft", "brave-hearted"]


# ---------------------------------------------------------------------------
# World model rules
# ---------------------------------------------------------------------------
def _step_rule(world: World) -> list[str]:
    out: list[str] = []
    pet = world.get("petunia")
    quest: Quest = world.facts["quest"]
    reward: Reward = world.facts["reward"]
    if pet.meters["steps"] < len(quest.path):
        idx = int(pet.meters["steps"])
        spot = quest.path[idx]
        sig = ("step", idx)
        if sig not in world.fired:
            world.fired.add(sig)
            pet.meters["steps"] += 1
            out.append(f"Petunia reached the {spot}.")
            if spot == "gate":
                pet.memes["fear"] += 1
            elif spot in {"stones", "ladder"}:
                pet.memes["bravery"] += 1
            elif spot in {"pond", "bushes", "hive"}:
                pet.memes["hope"] += 1
            elif spot == "moonbeam":
                pet.meters["found"] = 1
                pet.memes["joy"] += 2
                out.append(f"At the end of the path, Petunia found {reward.phrase}.")
    return out


def _helper_rule(world: World) -> list[str]:
    out: list[str] = []
    pet = world.get("petunia")
    helper: Entity = world.facts["helper"]
    quest: Quest = world.facts["quest"]
    reward: Reward = world.facts["reward"]
    if pet.meters.get("steps", 0) >= 1 and helper.meters.get("arrived", 0) < 1:
        helper.meters["arrived"] = 1
        sig = ("helper", helper.id)
        if sig not in world.fired:
            world.fired.add(sig)
            pet.memes["fear"] = max(0.0, pet.memes["fear"] - 1)
            pet.memes["bravery"] += 1
            out.append(quest.turn + ".")
            if helper.type == "snail":
                out.append("The snail whispered, 'Slow steps are still brave steps.'")
            elif helper.type == "firefly":
                out.append("The firefly winked, and the path did not seem so wide.")
            else:
                out.append("The bee hummed, 'Mind the wind, but keep your sweet aim.'")
    if pet.meters.get("found", 0) and not world.facts.get("resolved"):
        world.facts["resolved"] = True
        pet.memes["joy"] += 2
        pet.memes["bravery"] += 1
        out.append(f"Petunia held the {reward.label} high, and {quest.ending}.")
    return out


RULES = [_step_rule, _helper_rule]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            lines = rule(world)
            if lines:
                changed = True
                for line in lines:
                    world.say(line)


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
def introduce(world: World) -> None:
    pet = world.get("petunia")
    world.say(
        f"Petunia was a {pet.meters['size_desc']} flower-child who lived in {world.setting.place}."
    )
    world.say(
        f"She loved the soft {world.setting.mood} mornings, but her heart still fluttered when a big quest began."
    )


def start_quest(world: World) -> None:
    quest: Quest = world.facts["quest"]
    reward: Reward = world.facts["reward"]
    world.para()
    world.say(
        f"One day, Petunia had a brave little quest: {quest.verb}."
    )
    world.say(
        f"She wanted to carry home {reward.phrase}, though {quest.risk}."
    )


def take_first_steps(world: World) -> None:
    pet = world.get("petunia")
    quest: Quest = world.facts["quest"]
    world.para()
    world.say("So Petunia took one breath, then another, and went to the gate.")
    pet.meters["steps"] = 1
    pet.memes["fear"] += 1
    pet.memes["bravery"] += 1
    propagate(world)


def finish_quest(world: World) -> None:
    quest: Quest = world.facts["quest"]
    reward: Reward = world.facts["reward"]
    helper: Entity = world.facts["helper"]
    pet = world.get("petunia")
    world.para()
    if not world.facts.get("resolved"):
        propagate(world)
    world.say(
        f"In the end, Petunia came home with the {reward.label}, and {helper.label} stayed near the path like a kindly rhyme."
    )
    world.say(
        f"Her fear got small, her bravery got bright, and {quest.ending}."
    )


def tell(setting: Setting, quest: Quest, helper_key: str, reward: Reward,
         name: str = "Petunia", trait: str = "tiny") -> World:
    world = World(setting)

    pet = world.add(Entity(
        id="petunia",
        kind="character",
        type="flower-child",
        label=name,
        meters={"steps": 0.0, "size": 1.0, "size_desc": 1.0},
        memes={"bravery": 1.0, "fear": 0.0, "joy": 0.0, "hope": 0.0},
    ))
    pet.meters["size_desc"] = 1.0  # placeholder to keep the world model numeric
    helper_info = HELPERS[helper_key]
    helper = world.add(Entity(
        id=helper_key,
        kind="character",
        type=helper_info["kind"],
        label=helper_info["label"],
        meters={helper_info["meter"]: 1.0},
        memes={"kindness": 1.0},
    ))
    world.facts.update(quest=quest, helper=helper, reward=reward, trait=trait)

    pet.meters["size_desc"] = 1.0
    introduce(world)
    start_quest(world)
    take_first_steps(world)
    finish_quest(world)
    world.facts["petunia"] = pet
    return world


# ---------------------------------------------------------------------------
# Parametrization
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    quest: str
    helper: str
    name: str = "Petunia"
    trait: str = "tiny"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for q in QUESTS:
            for h in HELPERS:
                out.append((s, q, h))
    return out


def explain_rejection(setting: str, quest: str, helper: str) -> str:
    return f"(No story: the setting {setting}, quest {quest}, and helper {helper} do not fit the nursery-rhyme gate.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny nursery-rhyme story world about Petunia's brave quest."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
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
    combos = valid_combos()
    filtered = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.quest is None or c[1] == args.quest)
        and (args.helper is None or c[2] == args.helper)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, helper = rng.choice(sorted(filtered))
    return StoryParams(
        setting=setting,
        quest=quest,
        helper=helper,
        name=args.name or "Petunia",
        trait=args.trait or rng.choice(TRAITS),
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    q: Quest = world.facts["quest"]
    h: Entity = world.facts["helper"]
    return [
        f'Write a short nursery-rhyme story about Petunia and {h.label} on a brave quest.',
        f'Tell a gentle tale where Petunia must {q.verb} and learn bravery one step at a time.',
        f'Write a child-friendly story with Petunia, a helper, and a safe ending at the end of the path.',
    ]


def story_qa(world: World) -> list[QAItem]:
    q: Quest = world.facts["quest"]
    h: Entity = world.facts["helper"]
    r: Reward = world.facts["reward"]
    pet: Entity = world.facts["petunia"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"The story is about Petunia, a tiny flower-child on a brave quest.",
        ),
        QAItem(
            question=f"What did Petunia want to do on her quest?",
            answer=f"She wanted to {q.verb} and bring home {r.phrase}.",
        ),
        QAItem(
            question=f"Who helped Petunia along the way?",
            answer=f"{h.label.capitalize()} helped Petunia, and that made her feel braver.",
        ),
        QAItem(
            question="How did Petunia change by the end?",
            answer="She started out a little worried, but by the end her bravery was brighter and her fear had grown small.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is when you feel nervous but still do the kind or hard thing that needs doing.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission or journey to find, carry, or do something important.",
        ),
        QAItem(
            question="What is a flower?",
            answer="A flower is a plant that grows petals and can bloom in a garden.",
        ),
    ]


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
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(nursery_garden). setting(moon_path). setting(orchard_edge).
quest(dew_drop). quest(moon_bell). quest(honey_note).
helper(snail). helper(firefly). helper(bee).

path(nursery_garden, gate). path(nursery_garden, ladder). path(nursery_garden, pond). path(nursery_garden, arch).
path(moon_path, gate). path(moon_path, stones). path(moon_path, bushes). path(moon_path, moonbeam).
path(orchard_edge, gate). path(orchard_edge, apples). path(orchard_edge, fence). path(orchard_edge, hive).

quest_path(dew_drop, gate). quest_path(dew_drop, stones). quest_path(dew_drop, pond).
quest_path(moon_bell, gate). quest_path(moon_bell, bushes). quest_path(moon_bell, moonbeam).
quest_path(honey_note, gate). quest_path(honey_note, ladder). quest_path(honey_note, hive).

helper_for(dew_drop, snail).
helper_for(moon_bell, firefly).
helper_for(honey_note, bee).

valid(S, Q, H) :- setting(S), quest(Q), helper_for(Q, H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
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


# ---------------------------------------------------------------------------
# Generate / emit / main
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    quest = QUESTS[params.quest]
    helper = next(iter(HELPERS))
    for k in HELPERS:
        if k == params.helper:
            helper = k
            break
    reward = REWARDS[params.quest]
    world = tell(setting, quest, helper, reward, params.name, params.trait)
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
    StoryParams(setting="nursery_garden", quest="dew_drop", helper="snail", name="Petunia", trait="tiny"),
    StoryParams(setting="moon_path", quest="moon_bell", helper="firefly", name="Petunia", trait="gentle"),
    StoryParams(setting="orchard_edge", quest="honey_note", helper="bee", name="Petunia", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid setting/quest/helper combos.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.quest} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
