#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/six_twentieth_additive_toy_store_transformation_rhyme.py
=======================================================================================

A tiny storyworld for a toy-store rhyming tale with a twist:
a child goes into a toy store, asks for a special toy, learns a safer or better
way to transform it, and leaves with a changed toy and a changed feeling.

Seed words: six, twentieth, additive
Setting: toy store
Features: Transformation, Rhyme, Twist
Style: Rhyming Story
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Toy:
    id: str
    label: str
    phrase: str
    transformed_label: str
    mechanism: str
    sound: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Twist:
    id: str
    label: str
    clue: str
    reveal: str
    shift: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_change_color(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    toy = world.entities.get("toy")
    if not child or not toy:
        return out
    if child.meters["turns"] < THRESHOLD:
        return out
    sig = ("color", toy.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    toy.meters["changed"] += 1
    toy.memes["wonder"] += 1
    out.append("__color__")
    return out


def _r_apply_twist(world: World) -> list[str]:
    out: list[str] = []
    toy = world.entities.get("toy")
    if not toy or toy.meters["changed"] < THRESHOLD:
        return out
    sig = ("twist", toy.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["twist_applied"] = True
    out.append("__twist__")
    return out


CAUSAL_RULES = [Rule("color", "transformation", _r_change_color), Rule("twist", "story", _r_apply_twist)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    child: str
    child_gender: str
    parent: str
    toy: str
    twist: str
    seed: Optional[int] = None


CHILD_NAMES = ["Mia", "Noah", "Ava", "Leo", "Luna", "Finn", "Ivy", "Theo"]
TOY_CHOICES = {
    "blocks": Toy(
        id="blocks",
        label="blocks",
        phrase="a box of plain blocks",
        transformed_label="rainbow blocks",
        mechanism="sticker stars",
        sound="click-clack",
        tags={"toy", "transform"},
    ),
    "car": Toy(
        id="car",
        label="toy car",
        phrase="a shiny toy car",
        transformed_label="moon car",
        mechanism="light-up wheels",
        sound="vroom",
        tags={"toy", "transform"},
    ),
    "doll": Toy(
        id="doll",
        label="doll",
        phrase="a soft little doll",
        transformed_label="story doll",
        mechanism="tiny ribbon cape",
        sound="swish",
        tags={"toy", "transform"},
    ),
}
TWISTS = {
    "rhyme": Twist(
        id="rhyme",
        label="rhyme",
        clue="a little note that ended every line the same way",
        reveal="the note was a rhyme card from the shopkeeper",
        shift="the child began to speak in song",
        tags={"rhyme"},
    ),
    "twentieth": Twist(
        id="twentieth",
        label="twentieth",
        clue="a sign with a shiny twentieth star",
        reveal="the twentieth shelf hid the best surprise",
        shift="the best toy was not in the first row at all",
        tags={"twentieth"},
    ),
    "additive": Twist(
        id="additive",
        label="additive",
        clue="a jar marked additive",
        reveal="the jar held tiny sparkly beads to add, not a new toy",
        shift="the child learned to add one little piece instead of buying more",
        tags={"additive"},
    ),
}


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(CHILD_NAMES)


def rhyme_line(a: str, b: str) -> str:
    return f"{a} and {b}"


def tell(child: Entity, parent: Entity, toy: Toy, twist: Twist) -> World:
    world = World()
    world.add(child)
    world.add(parent)
    world.add(Entity(id="toy", kind="thing", type="toy", label=toy.label))
    child.memes["want"] += 1
    child.memes["joy"] += 1
    child.meters["turns"] += 1

    world.say(
        f"{child.id} went to the toy store with {parent.label_word}. "
        f"The shelves were tall, the aisle was bright, and every toy seemed to sing."
    )
    world.say(
        f"{child.id} saw {toy.phrase} and said, "
        f'"Please let me have it, this very day!" '
        f"The toy looked plain, but sweet as cream."
    )
    world.para()
    world.say(
        f"Then came the twist, in a glittering scene: {twist.clue}. "
        f"{twist.shift}, and {child.id} leaned in to see."
    )
    world.say(
        f'{parent.id} smiled and said, "One little change can make it new; '
        f"add one bright touch, and watch it shine for you.""
    )
    propagate(world, narrate=False)
    world.say(
        f"{child.id} added {toy.mechanism} to the toy, and soon it sang {toy.sound}. "
        f"Now it was called {toy.transformed_label}, neat and sweet."
    )
    world.para()
    world.say(
        f"The shopkeeper laughed, {child.id} clapped in delight, and the day "
        f"ended with a rhyming, shining sight."
    )
    child.memes["joy"] += 1
    child.memes["wonder"] += 1
    world.facts.update(
        child=child,
        parent=parent,
        toy=toy,
        twist=twist,
        transformed=True,
        twist_applied=True,
    )
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for toy_id in TOY_CHOICES:
        for twist_id in TWISTS:
            combos.append(("toy_store", toy_id, twist_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story set in a toy store that uses the words "six", "twentieth", and "additive".',
        f"Tell a child-friendly rhyme where {f['child'].id} finds {f['toy'].phrase} in a toy store and a twist changes the toy.",
        f"Write a short story with a transformation, a twist, and a happy rhyme ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    toy = f["toy"]
    twist = f["twist"]
    return [
        ("Where did the story happen?",
         "It happened in a toy store, where the shelves were full of bright playthings and the air felt exciting."),
        ("What did the child want at first?",
         f"{child.id} wanted {toy.phrase}. The toy looked plain, but it seemed special enough to bring home."),
        ("What changed the toy?",
         f"{parent.id} showed that one small addition could transform it. {toy.mechanism.capitalize()} made the toy become {toy.transformed_label}."),
        ("What was the twist?",
         f"The twist was about {twist.label}. {twist.reveal}, which changed how the child thought about the prize."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a toy store?",
         "A toy store is a shop where people can find dolls, blocks, cars, and other toys to play with."),
        ("What does transformation mean?",
         "Transformation means something changes into a new form or a new kind of thing."),
        ("What is a rhyme?",
         "A rhyme is when words sound alike at the end, like song parts that fit together."),
    ]


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
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


TOY_CHOICES_KEYS = list(TOY_CHOICES)
TWIST_KEYS = list(TWISTS)


@dataclass
class StoryParams:
    child: str
    child_gender: str
    parent: str
    toy: str
    twist: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Toy-store rhyming storyworld with a transformation and a twist.")
    ap.add_argument("--child")
    ap.add_argument("--gender", dest="child_gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mom", "dad"])
    ap.add_argument("--toy", choices=TOY_CHOICES_KEYS)
    ap.add_argument("--twist", choices=TWIST_KEYS)
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
    toy = args.toy or rng.choice(TOY_CHOICES_KEYS)
    twist = args.twist or rng.choice(TWIST_KEYS)
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or _pick_name(rng, child_gender)
    parent = args.parent or rng.choice(["mom", "dad"])
    if toy not in TOY_CHOICES or twist not in TWISTS:
        raise StoryError("Invalid toy or twist choice.")
    return StoryParams(child=child, child_gender=child_gender, parent=parent, toy=toy, twist=twist)


def generate(params: StoryParams) -> StorySample:
    if params.toy not in TOY_CHOICES:
        raise StoryError("Unknown toy.")
    if params.twist not in TWISTS:
        raise StoryError("Unknown twist.")
    toy = TOY_CHOICES[params.toy]
    twist = TWISTS[params.twist]
    child = Entity(id=params.child, kind="character", type=params.child_gender, role="child")
    parent = Entity(id=params.parent, kind="character", type="mother" if params.parent == "mom" else "father", role="parent")
    world = tell(child, parent, toy, twist)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
valid(toy_store, T, W) :- toy(T), twist(W).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("toy_store", "toy_store")]
    for tid in TOY_CHOICES:
        lines.append(asp.fact("toy", tid))
    for wid in TWISTS:
        lines.append(asp.fact("twist", wid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib

    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in ASP parity.")
        rc = 1
    try:
        sample = generate(StoryParams(child="Mia", child_gender="girl", parent="mom", toy="blocks", twist="rhyme"))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample)
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return rc


CURATED = [
    StoryParams(child="Mia", child_gender="girl", parent="mom", toy="blocks", twist="rhyme"),
    StoryParams(child="Leo", child_gender="boy", parent="dad", toy="car", twist="twentieth"),
    StoryParams(child="Ava", child_gender="girl", parent="mom", toy="doll", twist="additive"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {idx + 1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
