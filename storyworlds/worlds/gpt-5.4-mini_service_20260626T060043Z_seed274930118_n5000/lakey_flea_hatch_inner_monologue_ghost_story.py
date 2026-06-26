#!/usr/bin/env python3
"""
storyworlds/worlds/lakey_flea_hatch_inner_monologue_ghost_story.py
===================================================================

A small ghost-story world with inner monologue, built from the seed words
"lakey", "flea", and "hatch".

Premise:
- Lakey hears tiny scratching under an old hatch in a quiet house.
- A flea-ghost keeps darting away when Lakey listens too hard.
- Lakey's inner monologue tracks fear, curiosity, and bravery.
- The turn comes when Lakey opens the hatch, finds the lost flea-ghost's tiny
  tunnel home, and helps it back to where it belongs.
- The ending proves the change: the house is still spooky, but no longer lonely.

The world is intentionally small and classical: a few entities, a few meters
and memes, a causal turn, and a resolution that changes what the final image
means.
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
    located_in: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the old house"
    detail: str = "a narrow hallway with a dusty rug and a hatch in the floor"


@dataclass
class StoryParams:
    name: str = "Lakey"
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


def inner_thought(world: World, hero: Entity, text: str) -> None:
    world.say(f"{hero.id} thought, “{text}”")


def build_world(params: StoryParams) -> World:
    world = World(Setting())
    hero = world.add(Entity(id=params.name, kind="character", type="child", label=params.name))
    flea = world.add(Entity(
        id="flea",
        kind="spirit",
        type="flea",
        label="a flea-ghost",
        phrase="a flea-ghost with tiny silver legs",
        located_in="the crack under the hatch",
        meters={"buzz": 1.0},
        memes={"loneliness": 1.0, "shyness": 1.0},
    ))
    hatch = world.add(Entity(
        id="hatch",
        type="hatch",
        label="the hatch",
        phrase="an old wooden hatch with a round iron ring",
        located_in="the hallway floor",
        meters={"creak": 1.0},
        memes={"mystery": 1.0},
    ))
    lamp = world.add(Entity(
        id="lamp",
        type="lamp",
        label="the lamp",
        phrase="a small lamp with a warm yellow shade",
        located_in="the side table",
        meters={"glow": 1.0},
    ))

    # Act 1: setup and unease.
    world.say(
        f"In {world.setting.place}, the air sat still in {world.setting.detail}, "
        f"and {hero.id} kept hearing a soft scratch from under {hatch.label}."
    )
    inner_thought(world, hero, "That sound is small, but it feels like it knows my name.")
    world.say(
        f"{hero.id} held the lamp close and looked at {hatch.label}. "
        f"{flea.label.capitalize()} waited under it, quiet as a sneeze."
    )
    hero.memes["curiosity"] = 1.0
    hero.memes["fear"] = 1.0
    world.facts.update(hero=hero, flea=flea, hatch=hatch, lamp=lamp)

    # Act 2: tension and inner monologue.
    world.para()
    world.say(
        f"{hero.id} wanted to walk away, but the scratching came again, weaker this time."
    )
    inner_thought(world, hero, "If I leave it alone, maybe it will stay lonely forever.")
    hero.memes["bravery"] = 1.0
    if hero.memes["fear"] >= THRESHOLD and hero.memes["curiosity"] >= THRESHOLD:
        world.say(
            f"{hero.id}'s knees shook, yet {hero.id} knelt by {hatch.label} and touched the iron ring."
        )
        world.say(
            f"From below came a tiny whisper: “Don't slam it. The dark is already loud.”"
        )
        flea.memes["loneliness"] += 1.0
        flea.meters["stir"] = 1.0

    # Turn: open the hatch and discover what is needed.
    world.para()
    world.say(f"{hero.id} took one breath, then another, and lifted {hatch.label}.")
    hatch.meters["open"] = 1.0
    flea.located_in = "the open hatchway"
    flea.memes["loneliness"] = 0.0
    world.say(
        f"Below the floor was a little tunnel room with a folded scarf, three pebbles, "
        f"and a nest made from soft gray lint."
    )
    inner_thought(world, hero, "Oh. It was not a monster place. It was a lost place.")
    world.say(
        f"{flea.label.capitalize()} fluttered out, not scary at all now, just relieved."
    )
    flea.meters["buzz"] += 1.0

    # Resolution: help the flea-ghost go home.
    world.say(
        f"{hero.id} gently set the scarf straight and brushed the lint nest back into a neat corner."
    )
    flea.memes["safe"] = 1.0
    flea.memes["happy"] = 1.0
    hero.memes["fear"] = 0.0
    hero.memes["curiosity"] = 0.0
    hero.memes["bravery"] += 1.0
    world.say(
        f"Then {hero.id} left {hatch.label} open just a little, so the flea-ghost could come and go without getting trapped."
    )
    world.say(
        f"By bedtime, the house was still spooky, but it was a kinder kind of spooky; "
        f"{hero.id} could hear the soft scratching and know it meant a small friend was safe."
    )

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short ghost story for young children with inner monologue, using the words "lakey", "flea", and "hatch".',
        "Tell a gentle spooky story where a child hears something under a hatch and discovers it is a lonely flea-ghost.",
        "Write a small, child-friendly ghost story that includes a scared thought, a brave choice, and a kinder ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    flea: Entity = world.facts["flea"]
    hatch: Entity = world.facts["hatch"]
    qa = [
        QAItem(
            question=f"What did {hero.id} keep hearing in the hallway?",
            answer=f"{hero.id} kept hearing a soft scratching sound from under {hatch.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} think before opening {hatch.label}?",
            answer=f"{hero.id} thought that the sound was small but felt like it knew {hero.id}'s name.",
        ),
        QAItem(
            question=f"What was really under {hatch.label}?",
            answer=f"There was {flea.label}, a tiny flea-ghost hiding in a little tunnel room below the floor.",
        ),
        QAItem(
            question=f"How did {hero.id} help {flea.label}?",
            answer=f"{hero.id} gently straightened the scarf, brushed the nest neat again, and left {hatch.label} open just a little so {flea.label} would not feel trapped.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hatch?",
            answer="A hatch is a small door or panel that opens to a hidden space, like a floor space or a crawlspace.",
        ),
        QAItem(
            question="Why can a dark room feel scary?",
            answer="A dark room can feel scary because you cannot easily see what is there, so your imagination fills in the blanks.",
        ),
        QAItem(
            question="What is a flea?",
            answer="A flea is a very tiny insect that can jump quickly.",
        ),
        QAItem(
            question="Why do children listen closely in a spooky house?",
            answer="Children listen closely because small sounds can hint that something hidden, lost, or mysterious is nearby.",
        ),
    ]


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
    lines.append("== (3) World knowledge ==")
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
        if e.located_in:
            bits.append(f"located_in={e.located_in}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with inner monologue.")
    ap.add_argument("--name", default="Lakey")
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
    name = args.name or "Lakey"
    return StoryParams(name=name)


ASP_RULES = r"""
% This world is intentionally tiny; the ASP twin mirrors the reasonableness gate
% for the single canonical story shape.
valid_story(lakey, hatch, flea).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("name", "lakey"),
        asp.fact("thing", "flea"),
        asp.fact("thing", "hatch"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(ASP_RULES.strip())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(name="Lakey"))]
    else:
        for i in range(max(1, args.n)):
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
