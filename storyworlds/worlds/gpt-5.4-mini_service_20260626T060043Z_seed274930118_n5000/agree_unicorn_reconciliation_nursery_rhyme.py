#!/usr/bin/env python3
"""
Storyworld: agree / unicorn reconciliation nursery rhyme.

A small simulated story domain where a child and a unicorn have a tangle over
a moonlit toy, then find a soft reconciliation and agree again.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "child", "childling"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    name: str
    child_type: str
    toy: str
    setting: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


SETTINGS = {
    "nursery": "the nursery",
    "garden": "the little garden",
    "moonroom": "the moonlit room",
}

TOYS = {
    "starbell": "a tiny star bell",
    "crown": "a silver paper crown",
    "blanket": "a soft blanket",
    "lantern": "a round lantern",
}

NAMES = ["Maya", "Nina", "Lila", "Poppy", "Tessa", "Milo", "Theo", "Finn"]
CHILD_TYPES = {"girl", "boy"}


def _init_world(params: StoryParams) -> World:
    world = World(setting=SETTINGS[params.setting])
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.name))
    unicorn = world.add(Entity(id="unicorn", kind="character", type="unicorn", label="the unicorn"))
    toy = world.add(Entity(id="toy", kind="thing", type=params.toy, label=TOYS[params.toy], owner=child.id))
    toy.meters["shine"] = 1.0
    child.memes["wish"] = 1.0
    unicorn.memes["sparkle"] = 1.0
    world.facts.update(child=child, unicorn=unicorn, toy=toy, params=params)
    return world


def _setup(world: World) -> None:
    child = world.get("child")
    unicorn = world.get("unicorn")
    toy = world.get("toy")
    world.say(f"{child.label} was a little {child.type} with a kindly heart.")
    world.say(f"In {world.setting}, {child.pronoun('subject')} met {unicorn.label}, a unicorn with a bright, curly horn.")
    world.say(f"{child.label} loved {toy.label}, for it shone like a star in a nursery rhyme dream.")


def _conflict(world: World) -> None:
    child = world.get("child")
    unicorn = world.get("unicorn")
    toy = world.get("toy")
    child.meters["hold"] = 1.0
    unicorn.meters["want"] = 1.0
    child.memes["stubborn"] = 1.0
    unicorn.memes["wistful"] = 1.0
    world.say(f"Both {child.label} and {unicorn.label} wanted {toy.label} for the same sweet game.")
    world.say(f"{child.label} said, \"I want to keep it.\" {unicorn.label} said, \"I wish to hold it too.\"")
    world.say("The room grew quiet as a little tiff came to the door of the day.")


def _reconcile(world: World) -> None:
    child = world.get("child")
    unicorn = world.get("unicorn")
    toy = world.get("toy")
    child.memes["softness"] = 1.0
    unicorn.memes["softness"] = 1.0
    child.memes["stubborn"] = 0.0
    unicorn.memes["wistful"] = 0.0
    child.memes["agree"] = 1.0
    unicorn.memes["agree"] = 1.0
    toy.meters["held_together"] = 1.0
    world.say(f"Then the unicorn bowed its head, and {child.label} took a breath as small as a whisper.")
    world.say(f"They agreed to share {toy.label}, one turn each, like bells that ring together in a rhyme.")
    world.say(f"At once there was reconciliation: no one had lost, and both had smiles as warm as bread.")


def _ending(world: World) -> None:
    child = world.get("child")
    unicorn = world.get("unicorn")
    toy = world.get("toy")
    world.say(f"{child.label} laughed, {unicorn.label} pranced, and {toy.label} sparkled in the calm little air.")
    world.say(f"By the end, they could agree, and the day felt stitched up neat and bright.")


def tell(params: StoryParams) -> World:
    world = _init_world(params)
    _setup(world)
    world.lines.append("")
    _conflict(world)
    world.lines.append("")
    _reconcile(world)
    _ending(world)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        'Write a short nursery-rhyme story about a child and a unicorn who learn to agree.',
        f"Tell a gentle story in {world.setting} where {p.name} and a unicorn both want the same shiny toy, then reconcile.",
        f"Write a child-friendly rhyme with the words 'agree' and 'unicorn' about sharing {world.facts['toy'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child = world.facts["child"]
    toy = world.facts["toy"]
    return [
        QAItem(
            question=f"Who wanted {toy.label} in the story?",
            answer=f"{p.name} and the unicorn both wanted {toy.label}, so they had to sort out their little disagreement.",
        ),
        QAItem(
            question=f"What did {p.name} and the unicorn do at the end?",
            answer=f"They agreed to share {toy.label} and found reconciliation instead of a quarrel.",
        ),
        QAItem(
            question=f"Where did the story happen?",
            answer=f"The story happened in {world.setting}, where {child.label} met the unicorn.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a unicorn?",
            answer="A unicorn is a magical horse-like creature with one horn on its forehead.",
        ),
        QAItem(
            question="What does it mean to agree?",
            answer="To agree means to decide together that something is okay or fair for both people.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making peace after a disagreement and feeling friendly again.",
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
        lines.append(f"  {e.id:7} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
child_wants(T) :- toy(T).
unicorn_wants(T) :- toy(T).
conflict(T) :- child_wants(T), unicorn_wants(T).
reconciled(T) :- conflict(T), agree(T).
#show conflict/1.
#show reconciled/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TOYS:
        lines.append(asp.fact("toy", tid))
        lines.append(asp.fact("agree", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show conflict/1. #show reconciled/1."))
    atoms = {str(a) for a in model}
    if "conflict(toy)" in atoms and "reconciled(toy)" in atoms:
        print("OK: ASP twin sees conflict and reconciliation.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected atoms.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about a child and a unicorn learning to agree.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--child-type", choices=sorted(CHILD_TYPES))
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--setting", choices=SETTINGS)
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
    name = args.name or rng.choice(NAMES)
    child_type = args.child_type or rng.choice(["girl", "boy"])
    toy = args.toy or rng.choice(list(TOYS))
    setting = args.setting or rng.choice(list(SETTINGS))
    return StoryParams(name=name, child_type=child_type, toy=toy, setting=setting)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show conflict/1. #show reconciled/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for name in NAMES[:5]:
            params = StoryParams(name=name, child_type="girl" if name in {"Maya", "Nina", "Lila", "Poppy", "Tessa"} else "boy", toy="starbell", setting="nursery")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
