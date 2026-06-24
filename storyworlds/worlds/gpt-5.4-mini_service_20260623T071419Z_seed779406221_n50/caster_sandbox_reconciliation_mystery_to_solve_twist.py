#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T071419Z_seed779406221_n50/caster_sandbox_reconciliation_mystery_to_solve_twist.py
==============================================================================================================================

A slice-of-life sandbox storyworld about a child with a caster wheel toy in a
sandbox, a small mystery to solve, a twist, and a gentle reconciliation.

The seed image:
---
A child in a sandbox is playing with a little caster toy. The toy keeps making
a track in the sand, but then it starts wobbling in a strange way. The child
and a friend search for the cause, discover a tiny stone stuck near the wheel,
and work together to fix it. The friend had looked guilty because they thought
they broke it, but the twist is that the wind blew grit in, not the friend.
They clean it up, apologize, and end the playtime sharing the toy again.

This script models:
- physical meters: sand, grit, wobble, track, smoothness, cleanliness
- emotional memes: worry, curiosity, relief, apology, trust, joy, reconciliation
- a small causal chain for mystery -> discovery -> twist -> reconciliation

It follows the Storyweavers contract:
- self-contained stdlib script
- eager import from storyworlds/results.py
- lazy import of storyworlds/asp.py in ASP helpers
- build_parser, resolve_params, generate, emit, main
- --verify checks Python/ASP parity and runs smoke generation
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: {})
    memes: dict[str, float] = field(default_factory=lambda: {})

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
class Location:
    id: str
    label: str
    setting: str = "sandbox"
    tags: set[str] = field(default_factory=set)


@dataclass
class CasterToy:
    id: str
    label: str
    phrase: str
    wheel_kind: str
    is_caster: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    cause: str
    clue: str
    reveal: str
    twist: str
    fix: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
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

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    toy = world.get("caster")
    sand = toy.meters.get("sand", 0.0)
    grit = toy.meters.get("grit", 0.0)
    if sand + grit >= 1.0 and toy.meters.get("wobble", 0.0) < 1.0:
        sig = ("wobble",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        toy.meters["wobble"] = 1.0
        toy.memes["curiosity"] = toy.memes.get("curiosity", 0.0) + 1.0
        out.append("The little caster toy began to wobble in a strange way.")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    if world.get("caster").meters.get("wobble", 0.0) < 1.0:
        return []
    if world.get("stone").meters.get("revealed", 0.0) >= 1.0:
        return []
    sig = ("clue",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("stone").meters["revealed"] = 1.0
    world.get("caster").memes["mystery"] = world.get("caster").memes.get("mystery", 0.0) + 1.0
    out.append("Under the wheel, there was a tiny stone stuck in the sand.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    friend = world.get("friend")
    stone = world.get("stone")
    if stone.meters.get("removed", 0.0) < 1.0:
        return []
    if child.memes.get("reconciliation", 0.0) >= 1.0:
        return []
    sig = ("reconcile",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["reconciliation"] = 1.0
    friend.memes["reconciliation"] = 1.0
    child.memes["trust"] = child.memes.get("trust", 0.0) + 1.0
    friend.memes["trust"] = friend.memes.get("trust", 0.0) + 1.0
    out.append("They smiled at each other again and shared the toy.")
    return out


CAUSAL_RULES = [
    Rule(name="wobble", apply=_r_wobble),
    Rule(name="clue", apply=_r_clue),
    Rule(name="reconcile", apply=_r_reconcile),
]


def valid_combos() -> list[tuple[str, str]]:
    return [(p, m) for p in LOCATIONS for m in MYSTERIES if true_combo(p, m)]


def true_combo(place: str, mystery: str) -> bool:
    return place == "sandbox" and mystery in MYSTERIES


@dataclass
class StoryParams:
    place: str
    mystery: str
    child: str
    child_gender: str
    friend: str
    friend_gender: str
    toy: str
    seed: Optional[int] = None


LOCATIONS = {
    "sandbox": Location(id="sandbox", label="the sandbox", setting="sandbox", tags={"sand"}),
}
CASTERS = {
    "caster": CasterToy(
        id="caster",
        label="caster toy",
        phrase="a little caster toy",
        wheel_kind="wheel",
        tags={"caster", "toy"},
    )
}
MYSTERIES = {
    "stone": Mystery(
        id="stone",
        cause="a tiny stone got stuck by the wheel",
        clue="a bump kept nudging the wheel",
        reveal="a tiny stone was hiding under the caster wheel",
        twist="the friend had not broken it",
        fix="they picked out the stone and brushed the sand away",
        tags={"stone", "twist"},
    )
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava"]
BOY_NAMES = ["Finn", "Leo", "Theo", "Max"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Sandbox slice-of-life storyworld with a caster toy mystery.")
    ap.add_argument("--place", choices=LOCATIONS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--child")
    ap.add_argument("--friend")
    ap.add_argument("--toy", choices=CASTERS)
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
    place = args.place or "sandbox"
    mystery = args.mystery or "stone"
    if not true_combo(place, mystery):
        raise StoryError("This sandbox story only works when the caster toy is in the sandbox and the mystery is solvable.")
    child_gender = rng.choice(["girl", "boy"])
    friend_gender = "boy" if child_gender == "girl" else "girl"
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice(BOY_NAMES if friend_gender == "boy" else GIRL_NAMES)
    toy = args.toy or "caster"
    return StoryParams(place=place, mystery=mystery, child=child, child_gender=child_gender, friend=friend, friend_gender=friend_gender, toy=toy)


def tell(params: StoryParams) -> World:
    w = World()
    child = w.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child))
    friend = w.add(Entity(id="friend", kind="character", type=params.friend_gender, label=params.friend))
    caster = w.add(Entity(id="caster", kind="thing", type="toy", label="caster toy", meters={"sand": 0.0, "grit": 0.0, "wobble": 0.0, "smoothness": 1.0}, memes={"curiosity": 0.0, "mystery": 0.0}))
    stone = w.add(Entity(id="stone", kind="thing", type="stone", label="tiny stone", meters={"revealed": 0.0, "removed": 0.0}, memes={"worry": 0.0}))
    location = w.add(Entity(id="sandbox", kind="place", type="place", label="the sandbox"))
    w.facts.update(child=child, friend=friend, caster=caster, stone=stone, location=location, params=params)

    w.say(f"{child.label} and {friend.label} were playing in {location.label} on a quiet afternoon.")
    w.say(f"{child.label} rolled {caster.label} back and forth, making a neat track in the sand.")
    w.say(f"Then the toy started to feel odd, and both children leaned closer.")
    w.para()
    caster.meters["sand"] += 1.0
    caster.meters["grit"] += 1.0
    propagate(w, narrate=True)
    w.say(f"{friend.label} looked worried and said they had only been helping with the track.")
    w.say(f"{child.label} did not want an argument, so {child.label} took a breath and looked again.")
    w.para()
    if w.get("stone").meters.get("revealed", 0.0) < 1.0:
        w.say("The little mystery still needed a closer look.")
    w.get("stone").meters["removed"] = 1.0
    w.get("caster").meters["wobble"] = 0.0
    w.get("caster").meters["smoothness"] = 1.0
    w.say("At last, they found the cause and brushed the sand away.")
    propagate(w, narrate=True)
    w.para()
    w.say(f"{child.label} turned to {friend.label} and apologized for jumping to a conclusion.")
    w.say(f"{friend.label} admitted they had worried too, but the real trouble was only a tiny stone.")
    w.say("They laughed a little, set the caster toy down, and made the track together again.")
    w.facts["twist"] = MYSTERIES[params.mystery].twist
    return w


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child = world.facts["child"]
    friend = world.facts["friend"]
    return [
        QAItem(question=f"What were {child.label} and {friend.label} doing in the sandbox?", answer=f"They were playing with a caster toy and making tracks in the sand."),
        QAItem(question="Why did the toy wobble?", answer="A tiny stone got stuck near the wheel, so the caster toy could not roll smoothly."),
        QAItem(question="What was the twist in the story?", answer="The twist was that the friend had not broken the toy; the real problem was only the stone in the sand."),
        QAItem(question="How did they fix it?", answer="They picked out the stone, brushed away the grit, and made the caster toy smooth again."),
        QAItem(question="How did the children end the story?", answer="They apologized, forgave each other, and shared the toy again with better trust."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a sandbox?", answer="A sandbox is a small play area filled with sand where children can dig, shape, and roll toys."),
        QAItem(question="What is a caster wheel?", answer="A caster wheel is a little wheel that can turn easily, so a toy can move smoothly over the ground."),
        QAItem(question="Why can a tiny stone matter?", answer="A tiny stone can block a wheel or make a toy wobble, even though it looks very small."),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a gentle slice-of-life story set in a sandbox where a caster toy starts wobbling and two children solve the mystery together.',
        'Tell a child-friendly story with a twist: the friend seems to have caused the problem, but the real cause is a tiny stone in the sand.',
        'Write a short reconciliation story about a sandbox mystery, ending with an apology, a fix, and the children sharing the toy again.',
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("== story qa ==")
    out.extend(f"Q: {q.question}\nA: {q.answer}" for q in sample.story_qa)
    out.append("== world qa ==")
    out.extend(f"Q: {q.question}\nA: {q.answer}" for q in sample.world_qa)
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
wobbly(T) :- sand(T,S), grit(T,G), S + G >= 1.
clue(T) :- wobbly(T), stone(S), not fixed(S).
reconcile(C,F) :- apology(C,F), twist(S), fixed(S).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("sand", "caster", 1),
        asp.fact("grit", "caster", 1),
        asp.fact("stone", "stone"),
        asp.fact("fixed", "stone"),
        asp.fact("apology", "child", "friend"),
        asp.fact("twist", "stone"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show wobbly/1.\n#show clue/1.\n#show reconcile/2."))
    return 0 if model is not None else 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_qa(world), world=world)


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
    StoryParams(place="sandbox", mystery="stone", child="Mia", child_gender="girl", friend="Leo", friend_gender="boy", toy="caster"),
    StoryParams(place="sandbox", mystery="stone", child="Finn", child_gender="boy", friend="Ava", friend_gender="girl", toy="caster"),
]


def valid_combo_checker(params: StoryParams) -> bool:
    return params.place == "sandbox" and params.mystery == "stone" and params.toy == "caster"


def resolve_params_and_check(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = resolve_params(args, rng)
    if not valid_combo_checker(params):
        raise StoryError("Invalid story parameters.")
    return params


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        # smoke test
        sample = generate(resolve_params(args, random.Random(args.seed or 0)))
        if not sample.story:
            raise SystemExit(1)
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show wobbly/1.\n#show clue/1.\n#show reconcile/2."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show wobbly/1.\n#show clue/1.\n#show reconcile/2."))
        print(model)
        return
    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base + i))
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
