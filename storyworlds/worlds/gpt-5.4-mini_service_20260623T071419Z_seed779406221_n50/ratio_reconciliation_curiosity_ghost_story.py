#!/usr/bin/env python3
"""
storyworlds/worlds/ratio_reconciliation_curiosity_ghost_story.py
=================================================================

A small ghost-story world built from the seed word "ratio" and the paired
features of Reconciliation and Curiosity.

Premise:
- A child finds a strange ghost in an old house.
- The child is curious about the ghost and a small ratio puzzle matters to the
  haunting.
- The ghost and the child must reconcile by comparing the right amounts and
  sharing a light, ending with calm instead of fear.

The world keeps state in meters and memes, drives prose from simulated events,
and includes a Python reasonableness gate plus an inline ASP twin.

This is a self-contained stdlib-only storyworld script.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
        return self.label or self.id


@dataclass
class House:
    place: str
    floor: str
    room: str
    ratio_note: str
    hush: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Ghost:
    id: str
    label: str
    tint: str
    ratio_need: tuple[int, int]
    liking: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Light:
    id: str
    label: str
    phrase: str
    glow: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Reconciliation:
    id: str
    label: str
    method: str
    result: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, house: House) -> None:
        self.house = house
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
        clone = World(self.house)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_shiver(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    if ghost.meters["unease"] < THRESHOLD:
        return out
    sig = ("shiver",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child = world.get("child")
    child.memes["fear"] += 1
    out.append("The hallway went cold.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    child = world.get("child")
    if ghost.memes["trust"] < THRESHOLD or child.memes["kindness"] < THRESHOLD:
        return out
    sig = ("reconcile",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.memes["peace"] += 1
    child.memes["peace"] += 1
    child.memes["fear"] = 0
    ghost.meters["unease"] = 0
    out.append("The cold softened into a quiet, good kind of stillness.")
    return out


CAUSAL_RULES = [
    Rule(name="shiver", tag="physical", apply=_r_shiver),
    Rule(name="reconcile", tag="social", apply=_r_reconcile),
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


def ratio_ok(ghost: Ghost, lamp: Light) -> bool:
    return ghost.ratio_need == (2, 1) and lamp.id == "lantern"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in HOUSES:
        for ghost_id, ghost in GHOSTS.items():
            for light_id, light in LIGHTS.items():
                if ratio_ok(ghost, light):
                    combos.append((place, ghost_id, light_id))
    return combos


@dataclass
class StoryParams:
    place: str
    ghost: str
    light: str
    child_name: str
    child_gender: str
    trait: str
    seed: Optional[int] = None


HOUSES = {
    "old_house": House(
        place="the old house",
        floor="the front hall",
        room="the candle room",
        ratio_note="two little candles for one soft lamp",
        hush="The windows were grey, and the house held its breath.",
        tags={"house", "ratio"},
    ),
    "attic_house": House(
        place="the attic house",
        floor="the attic stairs",
        room="the toy room",
        ratio_note="two bright windows for one dim shadow",
        hush="The attic boards creaked like a sleepy song.",
        tags={"house", "attic", "ratio"},
    ),
}

GHOSTS = {
    "milo": Ghost(
        id="milo",
        label="the ghost of Milo",
        tint="pale blue",
        ratio_need=(2, 1),
        liking="a careful balance of two lights and one brave hand",
        tags={"ghost", "ratio", "curious"},
    ),
    "nell": Ghost(
        id="nell",
        label="the ghost of Nell",
        tint="silver",
        ratio_need=(2, 1),
        liking="two warm smiles for one lonely room",
        tags={"ghost", "ratio", "curious"},
    ),
}

LIGHTS = {
    "lantern": Light(
        id="lantern",
        label="lantern",
        phrase="a little lantern",
        glow="glowed like a calm moon",
        tags={"light"},
    ),
    "candle": Light(
        id="candle",
        label="candle",
        phrase="a candle",
        glow="flickered like a nervous wink",
        tags={"light"},
    ),
}

RECONCILIATIONS = {
    "share": Reconciliation(
        id="share",
        label="sharing the light",
        method="hold the lantern together",
        result="the room felt friendly again",
        tags={"reconciliation"},
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ava", "Zoe"]
BOY_NAMES = ["Leo", "Eli", "Noah", "Finn", "Theo"]
TRAITS = ["curious", "gentle", "brave", "quiet", "thoughtful"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with ratio and reconciliation.")
    ap.add_argument("--place", choices=HOUSES)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.ghost is None or c[1] == args.ghost)
              and (args.light is None or c[2] == args.light)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, ghost, light = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, ghost=ghost, light=light, child_name=name, child_gender=gender, trait=trait)


def tell(house: House, ghost_cfg: Ghost, light_cfg: Light, child_name: str, child_gender: str, trait: str) -> World:
    world = World(house)
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label=ghost_cfg.label))
    lamp = world.add(Entity(id="lantern", kind="thing", type="light", label=light_cfg.label))
    world.facts["child"] = child
    world.facts["ghost"] = ghost
    world.facts["light"] = lamp
    world.facts["house"] = house
    world.facts["trait"] = trait

    child.memes["curiosity"] += 1
    ghost.meters["unease"] += 1
    child.memes["kindness"] += 1

    world.say(f"{child_name} came to {house.place} on a night that felt hushed and thin.")
    world.say(f"The air in {house.floor} was still, and {house.ratio_note} seemed to wait in the dark.")
    world.say(f"{child_name} was {trait}, so {child.pronoun()} followed the soft sound of footsteps and found {ghost_cfg.label}.")
    world.say(f"The ghost shone {ghost_cfg.tint}, and {child_name} wondered why {ghost_cfg.label} kept returning to the shadowed room.")

    world.para()
    world.say(f"{child_name} lifted {light_cfg.phrase}, and {light_cfg.glow}.")
    world.say(f'{child_name} asked, "What are you waiting for?"')
    ghost.memes["worry"] += 1

    if ratio_ok(ghost_cfg, light_cfg):
        world.say(f'{ghost_cfg.label.capitalize()} whispered about a ratio: "Two lights for one lonely place makes the room feel steady."')
    else:
        world.say(f'{ghost_cfg.label.capitalize()} shook like fog because the balance was wrong.')

    world.para()
    if ratio_ok(ghost_cfg, light_cfg):
        child.memes["curiosity"] += 1
        ghost.memes["trust"] += 1
        world.say(f"{child_name} counted slowly and held the lantern at just the right height.")
        world.say(f"The ghost watched, then drifted closer, no longer shy.")
        prop = RECONCILIATIONS["share"]
        world.say(f'Together they chose {prop.method}, and {prop.result}.')
        propagate(world, narrate=True)
        world.say(f"At the end, {child_name} and {ghost_cfg.label} stood side by side, bright as if they had always belonged in the same room.")
    else:
        world.say(f"{child_name} tried to listen, but the room stayed lopsided and cold.")
        propagate(world, narrate=True)
        world.say(f"Even so, {child_name} promised to come back with the right light and a kinder question.")

    world.facts["ratio_ok"] = ratio_ok(ghost_cfg, light_cfg)
    world.facts["resolved"] = ratio_ok(ghost_cfg, light_cfg)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    ghost = f["ghost"]
    house = f["house"]
    trait = f["trait"]
    return [
        f'Write a gentle ghost story for a child named {child.label_word} about a ratio hidden in {house.place}.',
        f"Tell a curious story where {child.label_word}, who is {trait}, meets {ghost.label_word} and learns how the right ratio can calm a lonely room.",
        f'Write a short ghost story that uses the word "ratio" and ends with reconciliation instead of fear.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    ghost = f["ghost"]
    house = f["house"]
    trait = f["trait"]
    out = [
        QAItem(
            question=f"Who is the story about in {house.place}?",
            answer=f"It is about {child.label_word}, a {trait} child, and {ghost.label_word}, the ghost in the house.",
        ),
        QAItem(
            question=f"What did {child.label_word} notice about the room?",
            answer=f"{child.label_word} noticed that {house.ratio_note} mattered to the way the room felt.",
        ),
        QAItem(
            question=f"Why was {child.label_word} curious?",
            answer=f"{child.label_word} was curious because {ghost.label_word} seemed lonely, and curiosity made {child.pronoun()} ask a gentle question instead of running away.",
        ),
    ]
    if f.get("resolved"):
        out.extend([
            QAItem(
                question=f"How did {child.label_word} and {ghost.label_word} reconcile?",
                answer=f"They reconciled by sharing the lantern and keeping the right ratio of light to shadow. That made the room feel friendly again.",
            ),
            QAItem(
                question=f"What changed at the end of the story?",
                answer=f"The cold fear changed into peace, and {child.label_word} stood beside {ghost.label_word} without worry.",
            ),
        ])
    return out


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ratio?",
            answer="A ratio is a way to compare amounts, like two lights for one dark corner.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after things feel separated or uneasy.",
        ),
        QAItem(
            question="What does curiosity do?",
            answer="Curiosity helps someone ask questions and learn instead of turning away from something strange.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict((k, v) for k, v in e.meters.items() if v)} memes={dict((k, v) for k, v in e.memes.items() if v)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="old_house", ghost="milo", light="lantern", child_name="Mia", child_gender="girl", trait="curious"),
    StoryParams(place="attic_house", ghost="nell", light="lantern", child_name="Leo", child_gender="boy", trait="gentle"),
]


def explain_rejection() -> str:
    return "(No story: this world only works when the ghost and lantern fit the ratio puzzle.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, house in HOUSES.items():
        lines.append(asp.fact("house", pid))
        for t in sorted(house.tags):
            lines.append(asp.fact("tag", pid, t))
    for gid, ghost in GHOSTS.items():
        lines.append(asp.fact("ghost", gid))
        lines.append(asp.fact("ratio_need", gid, ghost.ratio_need[0], ghost.ratio_need[1]))
    for lid, light in LIGHTS.items():
        lines.append(asp.fact("light", lid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(H,G,L) :- house(H), ghost(G), light(L), ratio_need(G,2,1), L = lantern.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    p = set(valid_combos())
    a = set(asp_valid_combos())
    if p != a:
        print("MISMATCH")
        print("python:", sorted(p - a))
        print("asp:", sorted(a - p))
        return 1
    sample = generate(CURATED[0])
    if not sample.story:
        print("Smoke test failed")
        return 1
    print(f"OK: {len(p)} combos and smoke test passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    if params.place not in HOUSES or params.ghost not in GHOSTS or params.light not in LIGHTS:
        raise StoryError("Invalid parameters for this ghost story world.")
    world = tell(HOUSES[params.place], GHOSTS[params.ghost], LIGHTS[params.light], params.child_name, params.child_gender, params.trait)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} and {p.ghost} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
