#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/dimension_miscellaneous_escalator_foreshadowing_flashback_ghost_story.py
=============================================================================================

A small, child-facing ghost story world set on an escalator, with foreshadowing
and flashback as the narrative instruments.

Seed tale used to build the world:
---
On the escalator in the bright mall, Mina felt a cold draft before she saw
anything else. Her grandma had once told her that a little ghost used the moving
stairs to find lost things, and Mina had laughed.

Then, halfway up, a pale shape flickered beside the handrail. Mina got scared,
but the ghost was not there to frighten anyone. It was looking for a tiny blue
scarf it had dropped long ago. Mina remembered her grandma's story and the cold
draft made sense now. She pointed to the scarf caught near a step, and the ghost
smiled. The escalator carried Mina to the top, and the ghost drifted away happy.

World model:
---
- Place: escalator in a mall-like public space
- Physical meters: cold, motion, height, glow, wear, age
- Emotional memes: curiosity, fear, courage, relief, wonder, loneliness
- Narrative instruments:
  * Foreshadowing: a cold draft, a flicker, a far-off chime
  * Flashback: grandma's old story about the escalator ghost
- Resolution: the child helps the ghost recover a lost keepsake; fear turns into wonder
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    alive: bool = True

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the escalator"
    backdrop: str = "the mall"
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    name: str = "Mina"
    gender: str = "girl"
    parent: str = "grandma"
    clue: str = "cold draft"
    token: str = "blue scarf"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


SETTINGS = {
    "escalator": Setting(place="the escalator", backdrop="the mall", affords={"ghost_story"}),
}

GHOSTS = {
    "escalator_ghost": {
        "label": "a little ghost",
        "phrase": "a pale little ghost with a silver glow",
        "type": "ghost",
    }
}

TOKENS = {
    "blue_scarf": {
        "label": "blue scarf",
        "phrase": "a tiny blue scarf",
    }
}

NAMES = ["Mina", "Nora", "Lina", "Ada", "Ivy", "Maya", "Elsa", "Rose"]


def _init_meter_map(**items: float) -> dict[str, float]:
    return dict(items)


def _init_meme_map(**items: float) -> dict[str, float]:
    return dict(items)


def story_intro(world: World, child: Entity, parent: Entity, ghost: Entity, token: Entity) -> None:
    world.say(
        f"{child.id} rode {world.setting.place} in {world.setting.backdrop}, "
        f"holding the rail with careful fingers."
    )
    world.say(
        f"Before anything strange happened, {child.pronoun('subject')} noticed a {child.meters['cold']:.0f}-step feeling of cold "
        f"that made the air seem quieter than it should have been."
    )
    world.say(
        f"At the same time, {child.pronoun('subject')} remembered how {parent.label} had once whispered "
        f"that {ghost.label} liked to ride the moving stairs and look for lost things."
    )


def foreshadow(world: World, child: Entity, ghost: Entity) -> None:
    child.meters["cold"] += 1
    child.memes["curiosity"] += 1
    child.memes["wonder"] += 0.5
    world.say(
        f"A small draft slipped up the steps, and the handrail gave a soft hum as if it knew a secret."
    )
    world.say(
        f"That was the first hint that {ghost.label} might be close."
    )


def flashback(world: World, child: Entity, parent: Entity) -> None:
    child.memes["fear"] += 0.5
    child.memes["courage"] += 0.5
    world.say(
        f"{child.id} thought back to {parent.label}'s old story: a ghost that never wanted to scare anyone, "
        f"only to find the thing it had lost."
    )
    world.say(
        f"In that memory, {parent.label} had laughed gently and said that even a ghost could feel lonely."
    )


def reveal(world: World, child: Entity, ghost: Entity, token: Entity) -> None:
    ghost.meters["glow"] += 1
    ghost.memes["loneliness"] += 1
    world.say(
        f"Halfway up, a pale shape flickered beside the handrail."
    )
    world.say(
        f"It was {ghost.phrase}, and in its tiny hands there was no scare at all—only worry."
    )
    world.say(
        f"The ghost was searching for {token.phrase}, which had slipped into a narrow corner beside the moving steps long ago."
    )


def help_find_token(world: World, child: Entity, ghost: Entity, token: Entity) -> None:
    child.memes["courage"] += 1
    child.memes["fear"] = max(0.0, child.memes["fear"] - 0.5)
    ghost.memes["loneliness"] = max(0.0, ghost.memes["loneliness"] - 1)
    ghost.memes["relief"] += 1
    world.say(
        f"{child.id} remembered the old story and pointed carefully to {token.phrase} caught near a step."
    )
    world.say(
        f"The ghost floated down just enough to take it, and its glow warmed from pale silver to a soft, happy shine."
    )


def ending(world: World, child: Entity, parent: Entity, ghost: Entity, token: Entity) -> None:
    child.memes["relief"] += 1
    child.memes["wonder"] += 1
    world.say(
        f"By the time {child.id} reached the top, the last of the cold draft had faded."
    )
    world.say(
        f"{ghost.label} drifted away with {token.it()} tucked safely close, and {child.id} smiled because the ghost story had turned out kind after all."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS["escalator"])
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        traits=["small", "careful"],
        meters=_init_meter_map(cold=0.0, motion=0.0, height=0.0, wear=0.0),
        memes=_init_meme_map(curiosity=0.0, fear=0.0, courage=0.0, relief=0.0, wonder=0.0),
    ))
    parent = world.add(Entity(
        id="Grandma",
        kind="character",
        type="woman",
        label="grandma",
        meters=_init_meter_map(age=0.0),
        memes=_init_meme_map(warmth=1.0, memory=1.0),
    ))
    ghost = world.add(Entity(
        id="Ghost",
        kind="character",
        type="ghost",
        label="a little ghost",
        phrase="a pale little ghost with a silver glow",
        meters=_init_meter_map(glow=0.0, age=1.0),
        memes=_init_meme_map(loneliness=1.0, relief=0.0),
        alive=False,
    ))
    token = world.add(Entity(
        id="Scarf",
        kind="thing",
        type="scarf",
        label="blue scarf",
        phrase="a tiny blue scarf",
        owner=ghost.id,
        meters=_init_meter_map(wear=1.0),
    ))

    world.facts.update(child=child, parent=parent, ghost=ghost, token=token, params=params)

    story_intro(world, child, parent, ghost, token)
    world.para()
    foreshadow(world, child, ghost)
    flashback(world, child, parent)
    world.para()
    reveal(world, child, ghost, token)
    help_find_token(world, child, ghost, token)
    world.para()
    ending(world, child, parent, ghost, token)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short ghost story for a young child about {p.name} on an escalator, with a chilly hint that something unseen is near.',
        f"Tell a gentle escalator ghost story where {p.name} remembers a story from {p.parent} and helps a lonely ghost find its {p.token}.",
        f'Write a child-friendly story with foreshadowing and flashback, set on the escalator in the mall, ending with kindness instead of fear.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child: Entity = world.facts["child"]
    parent: Entity = world.facts["parent"]
    ghost: Entity = world.facts["ghost"]
    token: Entity = world.facts["token"]
    return [
        QAItem(
            question=f"Where did {p.name} ride when the story began?",
            answer=f"{p.name} rode the escalator in the mall, holding the rail carefully.",
        ),
        QAItem(
            question=f"What was the first clue that something strange might be nearby?",
            answer=f"The first clue was a cold draft and a quiet humming rail, which hinted that the little ghost might be close.",
        ),
        QAItem(
            question=f"What did {p.parent} say in the flashback?",
            answer=f"In the flashback, {p.parent} had said that the ghost liked to ride the moving stairs and look for lost things.",
        ),
        QAItem(
            question=f"What was the ghost looking for?",
            answer=f"The ghost was looking for {token.phrase}, which had slipped near the moving steps.",
        ),
        QAItem(
            question=f"How did {p.name} feel at the end?",
            answer=f"{p.name} felt relieved and wonder-filled, because the scary feeling turned into a kind ghost story instead.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an escalator?",
            answer="An escalator is a moving staircase that carries people up or down one step at a time.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a small hint that something important or surprising may happen later.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of the story that remembers something from before the present moment.",
        ),
        QAItem(
            question="Why can ghosts in stories be sad instead of scary?",
            answer="Ghosts in stories are sometimes sad because they are lonely or lost, and they may need help instead of causing trouble.",
        ),
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
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
child_near_ghost(C) :- child(C), on_escalator(C), cold_hint(C), flashback(C).
helpful(C) :- child(C), child_near_ghost(C), remembers_story(C).
resolved(C) :- helpful(C), finds_token(C).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("place", "escalator"),
        asp.fact("setting", "escalator", "mall"),
        asp.fact("child", "child"),
        asp.fact("on_escalator", "child"),
        asp.fact("ghost", "ghost"),
        asp.fact("cold_hint", "child"),
        asp.fact("flashback", "child"),
        asp.fact("remembers_story", "child"),
        asp.fact("finds_token", "child"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/1."))
    atoms = sorted(set(asp.atoms(model, "resolved")))
    expected = [("child",)]
    if atoms == expected:
        print("OK: ASP twin matches the Python story shape.")
        return 0
    print("MISMATCH between ASP and Python story shape:")
    print("  ASP:", atoms)
    print("  PY :", expected)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Ghost story world set on an escalator, with foreshadowing and flashback."
    )
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["grandma", "grandpa"])
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
    name = args.name or rng.choice(NAMES)
    gender = args.gender or "girl"
    parent = args.parent or "grandma"
    return StoryParams(name=name, gender=gender, parent=parent, seed=args.seed)


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
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/1."))
        print(sorted(set(asp.atoms(model, "resolved"))))
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(name=n, gender="girl", parent="grandma")) for n in NAMES[:5]]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
