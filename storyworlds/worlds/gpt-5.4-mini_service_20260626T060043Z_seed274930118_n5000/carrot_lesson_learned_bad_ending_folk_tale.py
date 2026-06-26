#!/usr/bin/env python3
"""
A small folk-tale storyworld about a carrot, a lesson learned, and a bad ending.

Seed tale inspiration:
---
A rabbit found a shining carrot in a garden and bragged that it was the finest prize in the world.
He ignored the old mole's warning, shared it with no one, and hid it where the fox could smell it.
By evening the carrot was gone, and the rabbit learned too late that greed makes a thin basket.
---

World model:
- Typed entities track physical meters and emotional memes.
- The carrot can be coveted, hidden, stolen, or spoiled.
- A warning may be ignored, which raises pride and leads to loss.
- The ending is intentionally bad: the hero learns a lesson, but does not recover the prize.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    hidden_in: Optional[str] = None
    stolen_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rabbit", "hare", "boy", "fox", "crow", "mole"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the old garden"
    things: list[str] = field(default_factory=lambda: ["garden bed", "hedge", "stone wall"])


@dataclass
class StoryParams:
    place: str = "garden"
    hero: str = "rabbit"
    rival: str = "fox"
    helper: str = "mole"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld about a carrot and a bad lesson learned.")
    ap.add_argument("--place", choices=["garden"], default="garden")
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
    return StoryParams(place=args.place or "garden", seed=args.seed)


def _setup_world(params: StoryParams) -> World:
    world = World(Setting(place="the old garden"))
    hero = world.add(Entity(id="Pip", kind="character", type=params.hero))
    rival = world.add(Entity(id="Vex", kind="character", type=params.rival))
    helper = world.add(Entity(id="Moss", kind="character", type=params.helper))
    carrot = world.add(Entity(
        id="carrot", type="carrot", label="carrot",
        phrase="a bright orange carrot", owner=hero.id, caretaker=hero.id
    ))
    return world


def tell(world: World) -> None:
    hero = world.get("Pip")
    rival = world.get("Vex")
    helper = world.get("Moss")
    carrot = world.get("carrot")

    world.say(
        f"In {world.setting.place}, there lived a little rabbit named {hero.id} who loved bright things."
    )
    world.say(
        f"One morning {hero.id} found {carrot.phrase} tucked under a leaf, and {hero.pronoun()} "
        f"declared it the finest prize in the whole old garden."
    )
    world.say(
        f"{hero.id} puffed up with pride and would not share even a nibble, though the old mole {helper.id} "
        f"warned that a treasure kept too tightly can slip away."
    )

    world.para()
    world.say(
        f"But {hero.id} would not listen. {hero.pronoun().capitalize()} hid the carrot beside the stone wall, "
        f"where the hungry fox {rival.id} could smell it."
    )
    carrot.hidden_in = "stone wall"
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0) + 1
    rival.memes["hungry"] = rival.memes.get("hungry", 0) + 1

    world.say(
        f"At dusk, {rival.id} crept close, found the hiding place, and snatched the carrot away before "
        f"{hero.id} could hop back."
    )
    carrot.stolen_by = rival.id
    carrot.meters["lost"] = 1
    hero.memes["shock"] = hero.memes.get("shock", 0) + 1
    hero.memes["sadness"] = hero.memes.get("sadness", 0) + 1

    world.para()
    world.say(
        f"{hero.id} sat in the dirt with empty paws and learned the hard lesson too late: a good thing "
        f"should be shared and guarded wisely, not bragged over."
    )
    world.say(
        f"The fox vanished with the carrot, the mole shook his head, and the garden grew quiet again."
    )

    world.facts.update(hero=hero, rival=rival, helper=helper, carrot=carrot)


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short folk tale for a young child that includes a carrot, a warning, and a lesson learned.',
        'Tell a simple story where a rabbit loses a prized carrot because of pride and bad choices.',
        'Write a gentle folk tale with a bad ending in which a character learns too late not to be greedy about a carrot.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    rival = world.facts["rival"]
    helper = world.facts["helper"]
    carrot = world.facts["carrot"]
    return [
        QAItem(
            question="Who found the carrot in the garden?",
            answer=f"{hero.id} the rabbit found the carrot first."
        ),
        QAItem(
            question="Who warned the rabbit about keeping the treasure too tightly?",
            answer=f"The old mole named {helper.id} gave the warning."
        ),
        QAItem(
            question="What happened to the carrot at the end?",
            answer=f"The fox named {rival.id} stole it, so the carrot was lost."
        ),
        QAItem(
            question="What lesson did the rabbit learn?",
            answer="The rabbit learned that a treasure should be shared and guarded wisely, not bragged over."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a carrot?",
            answer="A carrot is a crunchy orange vegetable that grows in the ground."
        ),
        QAItem(
            question="Why should food be shared carefully?",
            answer="Sharing helps keep everyone kind and happy, and it can stop greed from causing trouble."
        ),
        QAItem(
            question="What is a fox known for in folktales?",
            answer="In folktales, a fox is often clever, sly, and quick to grab a chance."
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
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.stolen_by:
            bits.append(f"stolen_by={e.stolen_by}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(pip).
helper(moss).
rival(vex).
carrot(carrot).

warning(helper,must_share).
pride(hero).
ignored_warning(hero) :- pride(hero).

lost_carrot :- ignored_warning(hero), rival(vex), carrot(carrot).
bad_ending :- lost_carrot.

#show bad_ending/0.
#show lost_carrot/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero", "pip"),
        asp.fact("helper", "moss"),
        asp.fact("rival", "vex"),
        asp.fact("carrot", "carrot"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show bad_ending/0.\n#show lost_carrot/0."))
    atoms = {a.name for a in model}
    if "bad_ending" in atoms and "lost_carrot" in atoms:
        print("OK: ASP twin matches the intended bad ending.")
        return 0
    print("MISMATCH: ASP twin did not derive the expected story outcome.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = _setup_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
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


CURATED = [StoryParams()]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show bad_ending/0.\n#show lost_carrot/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
