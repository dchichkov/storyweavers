#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/animosity_drool_magic_moral_value_comedy.py
===============================================================================================================

A small comedy storyworld about a tiny magical spat, a lot of drool, and one
good moral choice that fixes the mess.

Seed tale imagined from the prompt:
---
A little rabbit and a little fox both wanted the shiny magic spoon. The fox
felt annoyed because the rabbit kept bragging. The rabbit got nervous and
started drooling whenever the spoon sparkled. Then a silly spell turned the
drool into glittery bubbles all over the table. The fox wanted to laugh, but
the rabbit felt embarrassed and the argument grew.

At last, the fox admitted that showing off was rude. The rabbit stopped
bragging, wiped the table, and shared the spoon. The magic spoon shone even
brighter, because being kind made the room feel lighter.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ("drool", "mess", "shine"):
            self.meters.setdefault(k, 0.0)
        for k in ("animosity", "embarrassment", "mischief", "joy", "moral_value", "pride"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "rabbit", "cat"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "fox", "dog"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the kitchen"
    mood: str = "cozy"


@dataclass
class MagicalItem:
    id: str
    label: str
    phrase: str
    sparkle: str
    invites_drool: bool = False


@dataclass
class StoryParams:
    place: str
    item: str
    hero_a: str
    hero_b: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.lines = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def _rule_drool_spill(world: World) -> list[str]:
    out: list[str] = []
    item = world.facts["item_entity"]
    for ent in world.entities.values():
        if ent.kind != "character":
            continue
        if ent.meters["drool"] < THRESHOLD:
            continue
        sig = ("spill", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if item.carried_by == ent.id or world.facts.get("item_visible", False):
            world.get(item.id).meters["mess"] += 1
            out.append(f"A silly drool bubble landed on {item.label}.")
    return out


def _rule_moral_cools_animosity(world: World) -> list[str]:
    out: list[str] = []
    a = world.get(world.facts["hero_a"])
    b = world.get(world.facts["hero_b"])
    sig = ("moral", a.id, b.id)
    if sig in world.fired:
        return out
    if a.memes["moral_value"] >= THRESHOLD or b.memes["moral_value"] >= THRESHOLD:
        if a.memes["animosity"] >= THRESHOLD or b.memes["animosity"] >= THRESHOLD:
            world.fired.add(sig)
            a.memes["animosity"] = 0.0
            b.memes["animosity"] = 0.0
            out.append("The grumpy feeling shrank when someone chose kindness.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_rule_drool_spill, _rule_moral_cools_animosity):
            out = fn(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero_a = world.add(Entity(id=params.hero_a, kind="character", type=NAME_TYPES[params.hero_a], traits=["tiny", "proud"]))
    hero_b = world.add(Entity(id=params.hero_b, kind="character", type=NAME_TYPES[params.hero_b], traits=["tiny", "thoughtful"]))

    item_cfg = ITEMS[params.item]
    item = world.add(Entity(
        id=item_cfg.id,
        kind="thing",
        type="magic_item",
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        owner=hero_a.id,
    ))
    world.facts.update(hero_a=hero_a.id, hero_b=hero_b.id, item_entity=item, item_cfg=item_cfg, setting=setting)

    # Act 1
    world.say(f"At {setting.place}, {hero_a.id} and {hero_b.id} both spotted {item_cfg.phrase}.")
    world.say(f"{hero_a.id} loved showing off, and {hero_b.id} hated being ignored.")
    hero_a.memes["pride"] += 1
    hero_b.memes["animosity"] += 1

    world.para()

    # Act 2
    world.say(f"When {item_cfg.sparkle} flashed, {hero_a.id} started to drool in a very undignified way.")
    hero_a.meters["drool"] += 1
    if item_cfg.invites_drool:
        world.say(f"The magic was so shiny that {hero_a.pronoun()} drooled like a sleepy kitten.")
    else:
        world.say(f"It was still shiny enough to make {hero_a.pronoun()} look ridiculous.")
    world.say(f"{hero_b.id} tried not to laugh, which somehow made the argument worse.")
    propagate(world)

    world.para()

    # Act 3
    hero_b.memes["moral_value"] += 1
    world.say(f"Then {hero_b.id} took a breath and chose a kinder way.")
    world.say(f'"Let me help wipe that up," {hero_b.id} said, even though {hero_b.pronoun()} was still annoyed.')
    hero_a.memes["embarrassment"] += 1
    hero_a.memes["moral_value"] += 1
    hero_a.meters["drool"] = 0.0
    item.meters["mess"] = 0.0
    propagate(world)
    world.say(f"{hero_a.id} stopped bragging, {hero_b.id} stopped frowning, and {item.label} shone again.")
    world.say(f"The table looked silly, but the room felt lighter.")

    world.facts["resolved"] = True
    world.facts["item"] = item_cfg
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", mood="cozy"),
    "classroom": Setting(place="the classroom", mood="busy"),
    "garden": Setting(place="the garden", mood="sunny"),
}

ITEMS = {
    "spoon": MagicalItem(
        id="spoon",
        label="the magic spoon",
        phrase="the magic spoon",
        sparkle="its silver sparkle",
        invites_drool=True,
    ),
    "marble": MagicalItem(
        id="marble",
        label="the magic marble",
        phrase="the magic marble",
        sparkle="its rainbow glint",
        invites_drool=False,
    ),
    "cup": MagicalItem(
        id="cup",
        label="the magic cup",
        phrase="the magic cup",
        sparkle="its tiny golden shimmer",
        invites_drool=True,
    ),
}

NAME_TYPES = {
    "Bun": "rabbit",
    "Finn": "fox",
    "Mina": "cat",
    "Pip": "dog",
    "Tia": "girl",
    "Noa": "boy",
}

RABBIT_NAMES = ["Bun", "Mina", "Tia"]
FOX_NAMES = ["Finn", "Pip", "Noa"]
TRAITS = ["proud", "comic", "curious", "stubborn", "gentle"]


@dataclass
class StoryConfig:
    place: str
    item: str
    a: str
    b: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place in SETTINGS:
        for item in ITEMS:
            for a in NAME_TYPES:
                for b in NAME_TYPES:
                    if a == b:
                        continue
                    out.append((place, item, a, b))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about animosity, drool, magic, and moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hero-a", dest="hero_a", choices=NAME_TYPES)
    ap.add_argument("--hero-b", dest="hero_b", choices=NAME_TYPES)
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
    place = args.place or rng.choice(list(SETTINGS))
    item = args.item or rng.choice(list(ITEMS))
    a = args.hero_a or rng.choice(list(NAME_TYPES))
    b = args.hero_b or rng.choice([n for n in NAME_TYPES if n != a])
    if a == b:
        raise StoryError("The two heroes must be different characters.")
    return StoryParams(place=place, item=item, hero_a=a, hero_b=b)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short comedy story about {f['hero_a']} and {f['hero_b']} at {f['setting'].place} with a magical object.",
        f"Tell a funny story where drool causes a magical mess and kindness fixes the argument.",
        f"Create a child-friendly tale with animosity, drool, magic, and a moral choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a = world.get(f["hero_a"])
    b = world.get(f["hero_b"])
    item: MagicalItem = f["item"]
    return [
        QAItem(
            question=f"Why did {a.id} start drooling?",
            answer=f"{a.id} started drooling because {item.label} sparkled so brightly that {a.pronoun()} got silly and embarrassed.",
        ),
        QAItem(
            question=f"Why did {b.id} feel annoyed at first?",
            answer=f"{b.id} felt annoyed because {a.id} was showing off and ignoring {b.pronoun('object')}.",
        ),
        QAItem(
            question="What fixed the argument?",
            answer=f"The argument got better when {b.id} chose kindness, helped clean the mess, and {a.id} stopped bragging.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is drool?",
            answer="Drool is a little bit of saliva that can drip from a mouth, especially when someone is sleepy, hungry, or very silly.",
        ),
        QAItem(
            question="What does moral value mean in a story?",
            answer="Moral value means the kind choice or lesson that helps characters do the right thing, like sharing or being kind.",
        ),
        QAItem(
            question="What does magic do in a story?",
            answer="Magic can make impossible or surprising things happen, like making a spoon sparkle or turning a normal moment into a funny one.",
        ),
    ]


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


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"{e.id}: meters={meters} memes={memes}")
    out.append(f"fired={sorted(world.fired)}")
    return "\n".join(out)


ASP_RULES = r"""
hero(X) :- character(X).
at_risk(A) :- character(A), drool(A).
messes(Item) :- item(Item), drool(A), shiny(Item), character(A).
kindness_wins(A,B) :- moral(A), character(A), character(B), animosity(B).
#show hero/1.
#show at_risk/1.
#show messes/1.
#show kindness_wins/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for name, t in NAME_TYPES.items():
        lines.append(asp.fact("character", name))
        lines.append(asp.fact("type", name, t))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("shiny", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show hero/1."))
    if model is None:
        print("ASP failed.")
        return 1
    print("OK: ASP rules load.")
    return 0


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
        print(asp_program("#show hero/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show hero/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        combos = [
            StoryParams(place=p, item=i, hero_a=a, hero_b=b)
            for p, i, a, b in [
                ("the kitchen", "spoon", "Bun", "Finn"),
                ("the classroom", "marble", "Mina", "Pip"),
                ("the garden", "cup", "Tia", "Noa"),
            ]
        ]
        samples = [generate(p) for p in combos]
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
