#!/usr/bin/env python3
"""
storyworlds/worlds/tend_rough_misunderstanding_repetition_sharing_ghost_story.py
================================================================================

A small story world in a Ghost Story style: a child tends to something rough,
but a misunderstanding about a repeating ghostly sound is resolved through
sharing and care.

Seed idea:
---
A child hears a ghostly scratch in an old house and thinks the house is upset.
The child keeps tending a rough old blanket, but the sound repeats. The child
learns the "ghost" is only a kitten behind the wall, and the warmth returns when
they share the blanket and a lamp.

World model:
---
- Physical meters: roughness, warmth, dust, noise, comfort
- Emotional memes: fear, care, misunderstanding, patience, sharing, relief
- Typed entities include people, a house, a blanket, a lamp, and a hidden pet.
- The prose is driven by state changes, not a frozen template.
- The script includes a Python reasonableness gate plus a matching inline ASP
  twin, with registry facts emitted by asp_facts().

Contract notes:
---
- Lazy import of storyworlds/asp in ASP helpers.
- Eager import of storyworlds/results containers.
- Supports the standard CLI switches and verification flow.
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
    owner: str = ""
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ("roughness", "warmth", "dust", "noise", "comfort"):
            self.meters.setdefault(k, 0.0)
        for k in ("fear", "care", "misunderstanding", "patience", "sharing", "relief"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self) -> str:
        return "it" if self.kind != "character" else "they"


@dataclass
class Place:
    id: str
    label: str
    dim: str
    echoes: bool = False
    old: bool = False


@dataclass
class StoryParams:
    place: str
    child: str
    blanket: str
    lamp: str
    ghost_sound: str
    hidden_pet: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


@dataclass
class Rule:
    name: str
    apply: callable


def _r_reveal_pet(world: World) -> list[str]:
    out = []
    child = world.get("child")
    pet = world.get("pet")
    wall = world.get("wall")
    if world.get("blanket").meters["warmth"] >= THRESHOLD and world.get("lamp").meters["warmth"] >= THRESHOLD:
        sig = ("reveal",)
        if sig not in world.fired:
            world.fired.add(sig)
            pet.hidden = False
            child.memes["misunderstanding"] = max(0.0, child.memes["misunderstanding"] - 1.0)
            child.memes["relief"] += 1
            wall.meters["noise"] = 0.0
            out.append("__reveal__")
    return out


RULES = [Rule("reveal_pet", _r_reveal_pet)]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            if rule.apply(world):
                changed = True


SETTING = {
    "attic": Place("attic", "the old attic", "tight", echoes=True, old=True),
    "hall": Place("hall", "the dark hall", "long", echoes=True, old=True),
    "cottage": Place("cottage", "the little cottage", "small", echoes=False, old=True),
}

NAMES = ["Mia", "Noah", "Lena", "Finn", "Ivy", "Theo"]
BLANKETS = {
    "rough": ("a rough old blanket", 1.0),
    "wool": ("a thick wool blanket", 0.8),
    "patchwork": ("a patchwork quilt", 0.6),
}
LAMPS = {
    "lamp": ("a small lamp", 1.0),
    "lantern": ("a warm lantern", 1.0),
}
SOUNDS = {
    "scratch": "scratch-scratch",
    "tap": "tap-tap",
    "tend": "tend-tend",
}
PETS = {
    "kitten": "a sleepy kitten",
    "mouse": "a little mouse",
    "bird": "a small bird",
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for p in SETTING:
        for b in BLANKETS:
            for l in LAMPS:
                for pet in PETS:
                    out.append((p, b, l, pet))
    return out


def reason_ok(params: StoryParams) -> bool:
    return params.blanket in BLANKETS and params.lamp in LAMPS and params.hidden_pet in PETS


ASP_RULES = r"""
valid(P,B,L,Pet) :- place(P), blanket(B), lamp(L), pet(Pet).
sharing(A) :- warmth(B), warmth(L), child(A), blanket(B), lamp(L).
misunderstanding(C) :- noise(W), child(C), wall(W).
reveal :- sharing(_), not misunderstanding(_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTING:
        lines.append(asp.fact("place", p))
    for b in BLANKETS:
        lines.append(asp.fact("blanket", b))
    for l in LAMPS:
        lines.append(asp.fact("lamp", l))
    for pet in PETS:
        lines.append(asp.fact("pet", pet))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world: tend, rough, misunderstanding, repetition, sharing.")
    ap.add_argument("--place", choices=SETTING)
    ap.add_argument("--child")
    ap.add_argument("--blanket", choices=BLANKETS)
    ap.add_argument("--lamp", choices=LAMPS)
    ap.add_argument("--ghost-sound", choices=SOUNDS)
    ap.add_argument("--hidden-pet", choices=PETS)
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
    place = args.place or rng.choice(list(SETTING))
    blanket = args.blanket or rng.choice(list(BLANKETS))
    lamp = args.lamp or rng.choice(list(LAMPS))
    child = args.child or rng.choice(NAMES)
    hidden_pet = args.hidden_pet or rng.choice(list(PETS))
    ghost_sound = args.ghost_sound or rng.choice(list(SOUNDS))
    params = StoryParams(place=place, child=child, blanket=blanket, lamp=lamp, ghost_sound=ghost_sound, hidden_pet=hidden_pet)
    if not reason_ok(params):
        raise StoryError("No reasonable story for those choices.")
    return params


def tell(params: StoryParams) -> World:
    world = World(SETTING[params.place])
    child = world.add(Entity("child", kind="character", type="child", label=params.child))
    blanket = world.add(Entity("blanket", label=BLANKETS[params.blanket][0], phrase=BLANKETS[params.blanket][0]))
    lamp = world.add(Entity("lamp", label=LAMPS[params.lamp][0], phrase=LAMPS[params.lamp][0]))
    wall = world.add(Entity("wall", label="the wall", hidden=True))
    pet = world.add(Entity("pet", kind="character", type="pet", label=PETS[params.hidden_pet], hidden=True))
    world.facts.update(child=child, blanket=blanket, lamp=lamp, wall=wall, pet=pet, params=params)

    child.memes["fear"] += 1
    child.memes["misunderstanding"] += 1
    child.meters["roughness"] += 1
    wall.meters["noise"] += 1

    world.say(f"{params.child} was in {world.place.label}, where the air felt old and quiet.")
    world.say(f"They kept tending {blanket.label}, because {blanket.label} felt rough in their hands.")
    world.say(f"Then came a {params.ghost_sound} from the wall.")
    world.para()
    world.say(f"{params.child} thought the house was whispering on purpose, and their fear grew.")
    world.say(f"The same little sound came again and again, each time from the same side of the wall.")
    child.memes["misunderstanding"] += 1
    world.say(f"So {params.child} held the blanket tighter and listened harder, trying to understand.")
    world.para()

    blanket.meters["warmth"] += 1
    lamp.meters["warmth"] += 1
    child.memes["sharing"] += 1
    child.memes["patience"] += 1
    world.say(f"At last {params.child} shared the blanket with the lamp, and the room became warmer.")
    world.say(f"The light shone along the boards, and the rough corners stopped looking so scary.")
    propagate(world)
    if not pet.hidden:
        world.say(f"Behind the wall, a small kitten had been making the {params.ghost_sound} sound all along.")
        world.say(f"{params.child} laughed softly and shared the blanket with the kitten too.")
        child.memes["fear"] = 0.0
        child.memes["relief"] += 1
        child.memes["care"] += 1
    world.say(f"By the end, the old room was still rough, but it felt kind instead of haunted.")
    world.facts["resolved"] = not pet.hidden
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a ghost-story for a 3-to-5-year-old about {p.child} in {world.place.label}, using the words "tend" and "rough".',
        f"Tell a gentle haunted-house story where a repeated sound causes a misunderstanding, and sharing a blanket helps.",
        f'Write a small spooky story with repetition and a hidden pet, ending in warmth and sharing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child = world.facts["child"].label
    blanket = world.facts["blanket"].label
    answers = [
        QAItem(
            question=f"Why did {child} keep tending the blanket?",
            answer=f"{child} kept tending {blanket} because it was rough and needed care in the old room.",
        ),
        QAItem(
            question=f"What sound kept repeating in the story?",
            answer=f"The sound repeated as {p.ghost_sound}, again and again from the wall.",
        ),
        QAItem(
            question=f"What did {child} think the repeated sound meant at first?",
            answer=f"At first, {child} had a misunderstanding and thought the house was whispering on purpose.",
        ),
        QAItem(
            question=f"How did sharing change the ending?",
            answer=f"Sharing the blanket and the lamp made the room warmer, and the scary sound turned out to be a kitten.",
        ),
    ]
    return answers


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a misunderstanding?", answer="A misunderstanding is when someone thinks something means one thing, but it actually means something different."),
        QAItem(question="What is repetition?", answer="Repetition means something happens or is said again and again."),
        QAItem(question="What is sharing?", answer="Sharing means letting someone else use or enjoy something with you."),
        QAItem(question="Why can a lamp help in a spooky room?", answer="A lamp gives warm light, which makes dark places easier to see and less scary."),
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id:8} ({e.kind:10}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams("attic", "Mina", "rough", "lamp", "scratch", "kitten"),
    StoryParams("hall", "Noah", "wool", "lantern", "tap", "mouse"),
    StoryParams("cottage", "Ivy", "patchwork", "lamp", "scratch", "bird"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print("\n".join(str(t) for t in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
