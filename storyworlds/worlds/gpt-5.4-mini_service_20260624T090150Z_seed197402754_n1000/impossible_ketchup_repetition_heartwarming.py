#!/usr/bin/env python3
"""
storyworlds/worlds/impossible_ketchup_repetition_heartwarming.py
===============================================================

A small, standalone story world about an "impossible" ketchup bottle, a little
bit of repetition, and a warm ending where people help each other.

Premise:
- A child loves ketchup on a simple snack.
- The ketchup bottle feels impossible: it will not open, or it will not pour.
- The child keeps trying the same thing again and again.
- A caregiver notices the problem, changes the method, and the day becomes kind
  again.

This world is intentionally tiny and constraint-checked. It models a few typed
entities with physical meters and emotional memes, uses those state changes to
drive prose, and includes an inline ASP twin plus a Python reasonableness gate.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen table"


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    parent: str
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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_frustration(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    bottle = world.get("ketchup")
    if child.memes.get("try_again", 0) < THRESHOLD:
        return out
    if bottle.meters.get("stuck", 0) < THRESHOLD:
        return out
    sig = ("frustration",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["frustration"] = child.memes.get("frustration", 0) + 1
    out.append("The same little problem kept happening, and it made the child sigh.")
    return out


def _r_harmony(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    parent = world.get("parent")
    bottle = world.get("ketchup")
    if child.meters.get("served", 0) < THRESHOLD:
        return out
    if parent.meters.get("helped", 0) < THRESHOLD:
        return out
    sig = ("harmony",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    child.memes["frustration"] = 0
    bottle.meters["stuck"] = 0
    out.append("After help arrived, the problem was no longer a problem.")
    return out


CAUSAL_RULES = [Rule("frustration", _r_frustration), Rule("harmony", _r_harmony)]


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


def _attempt(world: World, child: Entity, bottle: Entity) -> None:
    child.meters["try"] = child.meters.get("try", 0) + 1
    child.memes["try_again"] = child.memes.get("try_again", 0) + 1
    if child.meters["try"] <= 3:
        world.say(f"{child.id} tried again.")
    else:
        world.say(f"{child.id} tried again and again.")
    propagate(world, narrate=True)


def predict_unstuck(world: World) -> bool:
    sim = world.copy()
    sim.get("ketchup").meters["stuck"] = 1
    sim.get("child").memes["try_again"] = 1
    propagate(sim, narrate=False)
    return sim.get("ketchup").meters.get("stuck", 0) == 0


def tell(place: Setting, hero_name: str, hero_gender: str, parent_type: str) -> World:
    world = World(place)
    child = world.add(Entity(id="child", kind="character", type=hero_gender, label=hero_name))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    ketchup = world.add(Entity(id="ketchup", kind="thing", type="ketchup", label="ketchup bottle", phrase="a bright red ketchup bottle"))
    snack = world.add(Entity(id="snack", kind="thing", type="snack", label="toast", phrase="a piece of toast"))

    child.memes["want"] = 1
    ketchup.meters["stuck"] = 1
    ketchup.meters["full"] = 1
    snack.meters["plain"] = 1

    world.say(f"{child.label} was sitting at {world.setting.place} with {snack.phrase}.")
    world.say(f"{child.label} loved ketchup, especially when it was on {snack.label}.")
    world.say(f"But the ketchup bottle looked impossible to open.")
    world.para()
    world.say(f"{child.label} reached for the bottle.")
    _attempt(world, child, ketchup)
    _attempt(world, child, ketchup)
    _attempt(world, child, ketchup)
    world.para()
    if not predict_unstuck(world):
        world.say(f"{child.label} frowned. \"It still won't work,\" {child.pronoun()} said.")
    world.say(f"The {parent_type} came over and saw the same stuck lid.")
    parent.meters["helped"] = 1
    world.say(f"\"Let's try a different way,\" said {parent.label}.")
    ketchup.meters["warmed"] = 1
    ketchup.meters["stuck"] = 0
    world.say(f"They warmed the bottle in warm water and tapped the cap gently.")
    child.meters["served"] = 1
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    world.say(f"At last, the ketchup came out in a neat red line.")
    world.say(f"{child.label} smiled and squeezed ketchup on the toast.")
    world.say(f"The impossible bottle was only stubborn, and the little snack became just right.")

    world.facts.update(child=child, parent=parent, ketchup=ketchup, snack=snack, place=place)
    return world


SETTINGS = {
    "kitchen table": Setting(place="the kitchen table"),
    "picnic blanket": Setting(place="the picnic blanket"),
    "diner booth": Setting(place="the diner booth"),
}

NAMES = {
    "girl": ["Mia", "Lily", "Nora", "Ava"],
    "boy": ["Leo", "Finn", "Ben", "Theo"],
}

PARENTS = ["mother", "father"]


def valid_places() -> list[str]:
    return list(SETTINGS)


def is_reasonable(place: str) -> bool:
    return place in SETTINGS


def explain_rejection(place: str) -> str:
    return f"(No story: {place!r} is not a supported place for this tiny ketchup scene.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming repetition story about an impossible ketchup bottle.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENTS)
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
    place = args.place or rng.choice(list(SETTINGS))
    if not is_reasonable(place):
        raise StoryError(explain_rejection(place))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(place=place, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.name, params.gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        'Write a short heartwarming story for a young child about an impossible ketchup bottle and repeated tries.',
        f"Tell a gentle story where {child.label} keeps trying to open ketchup at {world.setting.place} until someone helps.",
        f"Write a simple repetition story that ends with ketchup on toast and a happy smile.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, ketchup = f["child"], f["parent"], f["ketchup"]
    return [
        QAItem(
            question=f"What did {child.label} keep trying to do?",
            answer=f"{child.label} kept trying to open the ketchup bottle so the ketchup could go on the toast.",
        ),
        QAItem(
            question=f"Why did the scene feel impossible at first?",
            answer="It felt impossible because the ketchup bottle was stuck and would not open, even after repeated tries.",
        ),
        QAItem(
            question=f"How did the {parent.type} help?",
            answer=f"The {parent.type} helped by trying a different way, warming the bottle and tapping the cap gently.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer="The ketchup finally came out, and the child smiled because the snack was ready.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is ketchup?",
            answer="Ketchup is a thick red sauce that people often put on fries, toast, or other snacks.",
        ),
        QAItem(
            question="Why can a bottle feel impossible to open?",
            answer="A bottle can feel impossible to open when the lid is stuck or too hard to twist.",
        ),
        QAItem(
            question="What does warm water sometimes help with?",
            answer="Warm water can help loosen a stuck lid so it is easier to open.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
stuck(ketchup).
tries(child).
repetition(child,ketchup) :- tries(child), stuck(ketchup).
helped(parent) :- warm(parent), tap(parent).
resolved :- helped(parent), stuck(ketchup).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("stuck", "ketchup"),
        asp.fact("tries", "child"),
        asp.fact("warm", "parent"),
        asp.fact("tap", "parent"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show repetition/2. #show resolved/0."))
    atoms = set((s.name, len(s.arguments)) for s in model)
    expected = {("repetition", 2), ("resolved", 0)}
    if atoms == expected:
        print("OK: ASP twin matches the Python story logic.")
        return 0
    print("MISMATCH: ASP twin did not match expectations.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show repetition/2. #show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            params = StoryParams(place=place, name="Mia", gender="girl", parent="mother", seed=base_seed)
            samples.append(generate(params))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
