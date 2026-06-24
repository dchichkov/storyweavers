#!/usr/bin/env python3
"""
storyworlds/worlds/mink_moral_value_sharing_fable.py
=====================================================

A small fable-style story world about a mink learning the value of sharing.

Seed tale idea:
---
A mink loved to keep the brightest things for itself: the last sweet berries, the
softest moss, the shiniest pebble. One cold morning, a small neighbor came
hungry and asked for help. The mink hesitated, then shared. The day ended warm,
and the mink learned that sharing can make a little thing grow into something
kind.

World model:
---
- The mink has a physical stash of food and a warmth meter.
- A neighbor has hunger and comfort needs.
- Sharing lowers the mink's stash, raises the neighbor's comfort, and increases
  the mink's moral value (kindness / generosity meme).
- Refusing at first raises selfishness, but a later turn can resolve the tension.

The prose is generated from state changes rather than from a fixed paragraph
with swapped nouns.
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
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mink", "fox", "badger", "wolf"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the riverbank"
    weather: str = "cold"
    affords: set[str] = field(default_factory=lambda: {"share", "hoard", "help"})


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    abundance: str
    shares_well: bool = True


@dataclass
class Neighbor:
    id: str
    type: str
    label: str
    phrase: str
    need_word: str


@dataclass
class StoryParams:
    snack: str
    neighbor: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def _moral_up(world: World, who: Entity, amount: float = 1.0) -> None:
    who.memes["kindness"] = who.memes.get("kindness", 0.0) + amount
    who.memes["sharing"] = who.memes.get("sharing", 0.0) + amount


def _moral_down(world: World, who: Entity, amount: float = 1.0) -> None:
    who.memes["selfishness"] = who.memes.get("selfishness", 0.0) + amount


def _share_rule(world: World) -> list[str]:
    out = []
    mink = world.get("mink")
    neighbor = world.get("neighbor")
    snack = world.get("snack")
    if mink.meters.get("shares", 0.0) < THRESHOLD:
        return out
    sig = ("shared", snack.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    amount = min(1.0, mink.meters.get("snack", 0.0))
    mink.meters["snack"] = max(0.0, mink.meters.get("snack", 0.0) - amount)
    neighbor.meters["hunger"] = max(0.0, neighbor.meters.get("hunger", 0.0) - amount)
    neighbor.meters["comfort"] = neighbor.meters.get("comfort", 0.0) + amount
    _moral_up(world, mink, 1.5)
    out.append("__shared__")
    return out


def _help_rule(world: World) -> list[str]:
    out = []
    mink = world.get("mink")
    neighbor = world.get("neighbor")
    if mink.memes.get("kindness", 0.0) < THRESHOLD:
        return out
    sig = ("helped",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    neighbor.meters["comfort"] = neighbor.meters.get("comfort", 0.0) + 1.0
    mink.meters["warmth"] = mink.meters.get("warmth", 0.0) + 0.5
    out.append("__help__")
    return out


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_share_rule, _help_rule):
            items = rule(world)
            if items:
                changed = True
                produced.extend(items)
    return produced


SNACKS = {
    "berries": Snack("berries", "berries", "a small bowl of sweet berries", "few"),
    "bread": Snack("bread", "bread", "a warm crust of brown bread", "one"),
    "nuts": Snack("nuts", "nuts", "a pouch of crunchy nuts", "some"),
}

NEIGHBORS = {
    "vole": Neighbor("vole", "vole", "a little vole", "a little vole with cold paws", "hunger"),
    "rabbit": Neighbor("rabbit", "rabbit", "a young rabbit", "a young rabbit with a shaky smile", "hunger"),
    "duckling": Neighbor("duckling", "duckling", "a duckling", "a duckling who had lost its lunch", "hunger"),
}

SETTINGS = {
    "riverbank": Setting(place="the riverbank", weather="cold"),
}

NAMES = ["Milo", "Pip", "Tala", "Nina", "Bram", "Lumi"]
TRAITS = ["curious", "quiet", "proud", "careful", "bright"]


@dataclass
class ASPRegistry:
    pass


ASP_RULES = r"""
% A good fable is one where the mink has something to share and a neighbor is in need.
can_share(S) :- snack(S).
needs_help(N) :- neighbor(N).

valid_story(S, N) :- can_share(S), needs_help(N).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, snack in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        lines.append(asp.fact("snack_phrase", sid, snack.label))
    for nid, n in NEIGHBORS.items():
        lines.append(asp.fact("neighbor", nid))
        lines.append(asp.fact("neighbor_phrase", nid, n.label))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(s, n) for s in SNACKS for n in NEIGHBORS}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable about a mink learning to share.")
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--neighbor", choices=NEIGHBORS)
    ap.add_argument("--name")
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
    combos = [(s, n) for s in SNACKS for n in NEIGHBORS
              if (args.snack is None or s == args.snack)
              and (args.neighbor is None or n == args.neighbor)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    snack, neighbor = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    return StoryParams(snack=snack, neighbor=neighbor, name=name)


def _build_world(params: StoryParams) -> World:
    world = World(SETTINGS["riverbank"])
    mink = world.add(Entity(
        id="mink", kind="character", type="mink", label=params.name,
        meters={"snack": 1.0, "warmth": 0.5, "shares": 0.0},
        memes={"kindness": 0.0, "selfishness": 0.0, "desire": 1.0},
    ))
    neighbor_cfg = NEIGHBORS[params.neighbor]
    neighbor = world.add(Entity(
        id="neighbor", kind="character", type=neighbor_cfg.type,
        label=neighbor_cfg.label,
        phrase=neighbor_cfg.phrase,
        meters={"hunger": 1.0, "comfort": 0.0},
        memes={"hope": 0.0},
    ))
    snack_cfg = SNACKS[params.snack]
    snack = world.add(Entity(
        id="snack", type=params.snack, label=snack_cfg.label,
        phrase=snack_cfg.phrase, owner="mink", plural=(params.snack == "berries"),
        meters={"quantity": 1.0},
    ))

    world.facts.update(mink=mink, neighbor=neighbor, snack=snack, snack_cfg=snack_cfg,
                       neighbor_cfg=neighbor_cfg, setting=world.setting)

    world.say(f"{mink.label} was a small mink who loved to keep {snack.phrase} all to itself.")
    world.say(f"Each day at {world.setting.place}, {mink.label} guarded its little stash carefully.")
    world.para()

    world.say(f"One cold morning, {neighbor_cfg.label} came near with a hungry look.")
    world.say(f'"Could you spare a bite?" {neighbor_cfg.label} asked softly.')
    mink.memes["desire"] += 1.0
    _moral_down(world, mink, 1.0)
    world.say(f"{mink.label} held the food close and looked away, because sharing felt hard.")
    world.para()

    world.say(f"Then the mink saw how small and cold the neighbor was, and its heart turned.")
    mink.meters["shares"] = 1.0
    propagate(world)
    if mink.meters.get("snack", 0.0) < 1.0:
        world.say(f"{mink.label} broke the snack into a kind little portion and shared it.")
    if neighbor.meters.get("comfort", 0.0) > 0.0:
        world.say(f"{neighbor_cfg.label} smiled and grew warmer after the gift.")
    world.say(f"By evening, {mink.label} felt richer with kindness than it had felt with a full stash.")
    return world


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mink = f["mink"]
    snack_cfg = f["snack_cfg"]
    neighbor_cfg = f["neighbor_cfg"]
    return [
        f'Write a short fable for a young child about a mink named {mink.label} and the value of sharing.',
        f"Tell a gentle story where {mink.label} keeps {snack_cfg.phrase} at first, then learns to share with {neighbor_cfg.label}.",
        "Write a simple animal fable that ends with kindness feeling better than keeping everything.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mink = f["mink"]
    snack = f["snack"]
    snack_cfg = f["snack_cfg"]
    neighbor_cfg = f["neighbor_cfg"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {mink.label}, a small mink who learned a lesson about sharing.",
        ),
        QAItem(
            question=f"What did {mink.label} not want to do at first?",
            answer=f"{mink.label} did not want to share {snack_cfg.phrase} at first.",
        ),
        QAItem(
            question=f"Who came asking for help?",
            answer=f"{neighbor_cfg.label} came asking for a little bite because it was hungry.",
        ),
        QAItem(
            question=f"What changed after {mink.label} shared?",
            answer=f"{neighbor_cfg.label} became more comfortable, and {mink.label} felt kinder and warmer inside.",
        ),
        QAItem(
            question=f"Why did the mink finally give away some of the snack?",
            answer=(
                f"{mink.label} saw that {neighbor_cfg.label} was cold and hungry, so it chose kindness over keeping the snack all alone."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sharing?",
            answer="Sharing means giving some of what you have to someone else so they can enjoy it too.",
        ),
        QAItem(
            question="Why is kindness important?",
            answer="Kindness helps friends feel safe, cared for, and less lonely.",
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story, often with animals, that teaches a lesson.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


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
    StoryParams(snack="berries", neighbor="vole", name="Milo"),
    StoryParams(snack="bread", neighbor="rabbit", name="Pip"),
    StoryParams(snack="nuts", neighbor="duckling", name="Tala"),
]


def world_knowledge_for_asp() -> list[tuple[str, str]]:
    return [(s, n) for s in SNACKS for n in NEIGHBORS]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_story_for_validity() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible snack/neighbor combos:\n")
        for snack, neighbor in combos:
            print(f"  {snack:8} {neighbor}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.snack} with {p.neighbor}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
