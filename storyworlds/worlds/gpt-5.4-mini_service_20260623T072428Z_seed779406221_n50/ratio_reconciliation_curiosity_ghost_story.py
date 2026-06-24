#!/usr/bin/env python3
"""
storyworlds/worlds/ratio_reconciliation_curiosity_ghost_story.py
================================================================

A standalone story world for a gentle ghost story about a child, a curious
ratio puzzle, and a reconciliation with a lonely ghost.

Premise:
- A child finds two jars in an old attic room.
- The jars hold different numbers of glowing marbles.
- A ghost appears upset because the jars were split unfairly.
- Curiosity leads the child to count, compare, and understand the ratio.
- Reconciliation happens when the child helps make a fairer sharing.

The world uses typed entities with physical meters and emotional memes.
The story is driven by world state, not by a fixed paragraph template.

Theme words:
- ratio
- reconciliation
- curiosity
- ghost story
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Chamber:
    id: str
    label: str
    dim: str
    spooky: bool = True
    ratio_hint: tuple[int, int] = (0, 0)


@dataclass
class Ghost:
    id: str
    label: str
    name: str
    mood: str
    wants_ratio: tuple[int, int]
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class JarPair:
    id: str
    left: int
    right: int
    label: str
    glow: str
    ratio: tuple[int, int]


class World:
    def __init__(self, chamber: Chamber) -> None:
        self.chamber = chamber
        self.entities: dict[str, Entity] = {}
        self.ghost: Optional[Ghost] = None
        self.jars: Optional[JarPair] = None
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.chamber)
        c.entities = copy.deepcopy(self.entities)
        c.ghost = copy.deepcopy(self.ghost)
        c.jars = copy.deepcopy(self.jars)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


def ratio_text(a: int, b: int) -> str:
    return f"{a}:{b}"


def compare_ratio(a: int, b: int) -> str:
    if a == b:
        return "equal"
    return "bigger" if a > b else "smaller"


def fair_share(left: int, right: int) -> tuple[int, int]:
    total = left + right
    if total % 2 == 0:
        half = total // 2
        return half, half
    return total // 2, total // 2 + 1


def maybe_reconcile(world: World, child: Entity, ghost: Ghost, jars: JarPair) -> bool:
    if child.memes["curiosity"] < THRESHOLD:
        return False
    child.memes["understanding"] += 1
    left, right = fair_share(jars.left, jars.right)
    if (left, right) == (jars.left, jars.right):
        return False
    ghost.meters["moved"] += 1
    ghost.memes["softness"] += 1
    jars.left, jars.right = left, right
    return True


def tell_story(world: World, child: Entity, parent: Entity, ghost: Ghost, jars: JarPair) -> None:
    world.say(
        f"On a dim evening in the old attic room, {child.id} found two glowing jars on a dusty shelf."
    )
    world.say(
        f"{jars.label.capitalize()} shimmered in the dark, and {child.id} noticed their ratio was {ratio_text(jars.left, jars.right)}."
    )
    child.memes["curiosity"] += 1
    child.memes["wonder"] += 1
    ghost.meters["restless"] += 1
    ghost.memes["loneliness"] += 1
    world.say(
        f"Then a pale ghost drifted down from the rafters. {ghost.name} looked sad, because the jars had been shared unevenly."
    )
    world.para()
    world.say(
        f'"Why are they not the same?" {child.id} asked, peering closer. '
        f"{child.pronoun().capitalize()} wanted to count again and understand the little pattern."
    )
    world.say(
        f"{parent.pronoun().capitalize()} knelt beside {child.id} and said, "
        f'"Sometimes a fair answer starts with a good question."'
    )
    if jars.left != jars.right:
        world.say(
            f"{child.id} counted the glowing marbles one by one, and the numbers felt like a tiny puzzle in {child.pronoun('possessive')} hands."
        )
    world.para()
    if maybe_reconcile(world, child, ghost, jars):
        child.memes["reconciliation"] += 1
        ghost.memes["reconciliation"] += 1
        child.memes["joy"] += 1
        ghost.memes["peace"] += 1
        world.say(
            f"{child.id} gently rearranged the marbles until both jars held {jars.left} glowing stones each."
        )
        world.say(
            f"The ghost's face softened at once. {ghost.name} bowed low, and the room felt less cold."
        )
        world.say(
            f'"That is fair," whispered the ghost. {child.id} smiled back, glad the question had led to peace.'
        )
    else:
        world.say(
            f"{child.id} kept thinking, but the jars already matched, so the ghost simply drifted away with a quiet nod."
        )
    world.para()
    if jars.left == jars.right:
        ending = f"The jars now matched in a neat {ratio_text(jars.left, jars.right)}."
    else:
        ending = f"The jars still held an uneven {ratio_text(jars.left, jars.right)}."
    world.say(
        f"By the end, the attic was calm again, the ghost was gentle, and {child.id} left with {ending}"
    )
    world.facts.update(child=child, parent=parent, ghost=ghost, jars=jars)


SETTINGS = {
    "attic": Chamber(id="attic", label="the attic room", dim="dusty", spooky=True, ratio_hint=(3, 1)),
    "library": Chamber(id="library", label="the candlelit library", dim="quiet", spooky=True, ratio_hint=(2, 1)),
    "hall": Chamber(id="hall", label="the old hall", dim="echoing", spooky=True, ratio_hint=(4, 2)),
}

GHOSTS = {
    "moth": Ghost(id="moth", label="ghost", name="Mara", mood="sad", wants_ratio=(1, 1)),
    "bell": Ghost(id="bell", label="ghost", name="Bram", mood="lonely", wants_ratio=(2, 2)),
    "lace": Ghost(id="lace", label="ghost", name="Lina", mood="worried", wants_ratio=(3, 3)),
}

JARS = {
    "marbles": JarPair(id="marbles", left=3, right=1, label="the jars", glow="soft green light", ratio=(3, 1)),
    "candles": JarPair(id="candles", left=2, right=1, label="the jars", glow="blue candle glow", ratio=(2, 1)),
    "pebbles": JarPair(id="pebbles", left=4, right=2, label="the jars", glow="silver pebble shine", ratio=(4, 2)),
}

CHILD_NAMES = ["Lily", "Maya", "Noah", "Eli", "Zoe", "Nora", "Finn", "Ava"]
PARENT_NAMES = ["mother", "father"]
TRAITS = ["curious", "careful", "kind", "quiet"]


@dataclass
class StoryParams:
    setting: str
    ghost: str
    jars: str
    child: str
    child_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, g, j) for s in SETTINGS for g in GHOSTS for j in JARS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Gentle ghost story about ratio, curiosity, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--jars", choices=JARS)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_NAMES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combo = valid_combos()
    filtered = [c for c in combo if (args.setting is None or c[0] == args.setting)
                and (args.ghost is None or c[1] == args.ghost)
                and (args.jars is None or c[2] == args.jars)]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    setting, ghost, jars = rng.choice(filtered)
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, ghost=ghost, jars=jars, child=child, child_gender=child_gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    chamber = SETTINGS[params.setting]
    world = World(chamber)
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, traits=[params.trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=params.parent))
    ghost = copy.deepcopy(GHOSTS[params.ghost])
    jars = copy.deepcopy(JARS[params.jars])
    world.ghost = ghost
    world.jars = jars
    tell_story(world, child, parent, ghost, jars)
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
    child, ghost, jars = f["child"], f["ghost"], f["jars"]
    return [
        f'Write a gentle ghost story for a young child that includes the word "ratio" and shows a child asking why {jars.label} are uneven.',
        f"Tell a spooky-but-kind story where {child.id} meets a lonely ghost, counts the jars, and solves the ratio puzzle with curiosity.",
        f"Write a child-friendly ghost story about reconciliation after a ghost sees an unfair ratio in two glowing jars.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, ghost, jars = f["child"], f["ghost"], f["jars"]
    return [
        QAItem(
            question=f"Who found the glowing jars in the attic?",
            answer=f"{child.id} found the glowing jars in the attic room and became curious about their ratio.",
        ),
        QAItem(
            question=f"Why did the ghost feel upset at first?",
            answer=f"The ghost felt upset because the jars had an uneven ratio and did not look fair.",
        ),
        QAItem(
            question=f"What did {child.id} do with the marbles?",
            answer=f"{child.id} counted the marbles carefully and helped make the jars fairer.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with reconciliation: the ghost grew peaceful, and the attic room felt calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ratio?",
            answer="A ratio tells how one amount compares with another amount.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to ask questions, look closer, and learn more.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making peace again after a problem or disagreement.",
        ),
        QAItem(
            question="Why are ghosts often used in ghost stories?",
            answer="Ghosts are often used in ghost stories to make the setting spooky while still allowing a gentle lesson or mystery.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.type}) memes={dict(e.memes)} meters={dict(e.meters)}")
    if world.ghost:
        lines.append(f"  ghost    (ghost) memes={dict(world.ghost.memes)} meters={dict(world.ghost.meters)}")
    if world.jars:
        lines.append(f"  jars     (thing) ratio={world.jars.left}:{world.jars.right}")
    return "\n".join(lines)


ASP_RULES = r"""
ratio(A,B) :- left(A,B), right(A,B).
uneven(A,B) :- left(A,X), right(A,Y), X != Y.
fair(A,B) :- left(A,X), right(A,X).
curious_child(C) :- curiosity(C).
reconcile(C,G) :- curious_child(C), uneven(A,B), fair(A,B).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for gid in GHOSTS:
        lines.append(asp.fact("ghost", gid))
    for jid, j in JARS.items():
        lines.append(asp.fact("jarpair", jid))
        lines.append(asp.fact("left", jid, j.left))
        lines.append(asp.fact("right", jid, j.right))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show ratio/2.\n#show fair/2.\n#show uneven/2."))
    return 0 if model is not None else 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show ratio/2.\n#show fair/2.\n#show uneven/2."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(setting=s, ghost=g, jars=j, child="Lily", child_gender="girl", parent="mother", trait="curious")) for s, g, j in valid_combos()]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
