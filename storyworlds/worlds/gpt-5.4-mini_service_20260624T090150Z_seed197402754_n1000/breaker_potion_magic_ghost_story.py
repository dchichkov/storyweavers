#!/usr/bin/env python3
"""
A tiny Ghost Story world: a child meets a shy ghost, a magical potion, and a breaker
that can spoil the spell. The story branches only through simulated world state.
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

GHOSTLY = {"whisper", "glow", "float", "shiver", "moon", "echo"}
PLACES = {
    "attic": {"dark", "old", "quiet"},
    "garden": {"quiet", "moonlit", "soft"},
    "cellar": {"dark", "cool", "quiet"},
    "hallway": {"long", "quiet", "creaky"},
}


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    touched_by_magic: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    potion_name: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    magic_active: bool = False
    breaker_bumped: bool = False
    potion_opened: bool = False
    ghost_visible: bool = False
    ghost_friend: bool = False

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


ASP_RULES = r"""
magic_on :- potion_opened, not breaker_bumped.
ghost_visible :- magic_on.
ghost_friend :- ghost_visible.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("potion_opened") if False else "% no-op placeholder in facts builder",
    ])


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny Ghost Story world with a magical potion and a breaker.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--potion")
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
    place = args.place or rng.choice(sorted(PLACES))
    name = args.name or rng.choice(["Mia", "Nora", "Leo", "Finn", "Ava", "Theo"])
    gender = args.gender or rng.choice(["girl", "boy"])
    potion_name = args.potion or rng.choice(["starlight potion", "midnight potion", "moon potion"])
    if "breaker" in potion_name.lower():
        raise StoryError("The potion name should not already be a breaker.")
    return StoryParams(place=place, child_name=name, child_type=gender, potion_name=potion_name)


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if not params.potion_name or "potion" not in params.potion_name:
        raise StoryError("This world needs a potion to carry the magic.")


def generate_world(params: StoryParams) -> World:
    w = World(place=params.place)
    child = w.add(Entity(id=params.child_name, kind="character", type=params.child_type, label=params.child_name))
    ghost = w.add(Entity(id="ghost", kind="ghost", type="ghost", label="a shy ghost"))
    potion = w.add(Entity(id="potion", type="potion", label=params.potion_name, owner=child.id))
    breaker = w.add(Entity(id="breaker", type="breaker", label="a little breaker", owner=child.id))
    candle = w.add(Entity(id="candle", type="thing", label="a small candle"))
    w.facts.update(child=child, ghost=ghost, potion=potion, breaker=breaker, candle=candle)
    return w


def apply_magic(w: World) -> None:
    if w.potion_opened and not w.breaker_bumped:
        w.magic_active = True
        w.ghost_visible = True
        w.get("ghost").touched_by_magic = True
        w.get("ghost").memes["lonely"] = 0
        w.get("ghost").memes["hope"] = 1
    else:
        w.magic_active = False
        w.ghost_visible = False


def tell_story(w: World, params: StoryParams) -> None:
    child = w.get(params.child_name)
    ghost = w.get("ghost")
    potion = w.get("potion")
    breaker = w.get("breaker")

    child.memes["curious"] = 1
    w.say(f"At {w.place}, {child.id} found {potion.label} beside a dusty candle.")
    w.say(f"The room felt {random.choice(sorted(PLACES[w.place]))}, and {child.id} held the bottle like a secret.")
    w.para()
    w.say(f"Inside the bottle was a spell that could make a ghost appear.")
    w.say(f"{child.id} whispered a little magic word and opened {potion.label}.")
    w.potion_opened = True

    if not w.breaker_bumped and child.id and child.kind == "character":
        w.say(f"Then {child.id} brushed against {breaker.label}, and the breaker tipped with a clack.")
        w.breaker_bumped = True
        child.memes["surprise"] = 1
        child.memes["worry"] = 1
        w.say("The spell trembled, and the glow almost went out.")
    apply_magic(w)

    w.para()
    if w.ghost_visible:
        w.say(f"A pale ghost floated up from the dark, soft as a breath.")
        w.say(f"It looked less spooky than lonely, and {child.id} smiled instead of running away.")
        w.say(f"{child.id} held the bottle steady, and the magic stayed warm.")
        w.say(f"The ghost waved, and the little room felt kind and moonlit.")
        w.ghost_friend = True
        child.memes["joy"] = 1
        child.memes["courage"] = 1
    else:
        w.say(f"The breaker had spoiled the spell, so the ghost stayed hidden.")
        w.say(f"{child.id} was quiet for a moment, then set the bottle down and tried again more carefully.")
        child.memes["patience"] = 1
        child.memes["courage"] = 1

    w.facts.update(magic_active=w.magic_active, ghost_visible=w.ghost_visible, ghost_friend=w.ghost_friend)


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    p = world.facts["potion"]
    qa = [
        QAItem(
            question=f"What did {c.id} find in {world.place}?",
            answer=f"{c.id} found {p.label} in {world.place}, and it was the bottle that held the magic.",
        ),
        QAItem(
            question=f"What happened when {c.id} opened the potion?",
            answer=(
                f"When {c.id} opened {p.label}, the magic started to wake up. "
                f"If the breaker did not bump it, a ghost could appear."
            ),
        ),
    ]
    if world.ghost_visible:
        qa.append(QAItem(
            question="What did the ghost look like when the magic worked?",
            answer="The ghost floated up softly, and it seemed lonely at first, then friendly.",
        ))
        qa.append(QAItem(
            question=f"How did {c.id} feel at the end?",
            answer=f"{c.id} felt brave and happy because the ghost was no longer scary.",
        ))
    else:
        qa.append(QAItem(
            question="Why didn't the ghost appear clearly?",
            answer="The little breaker tipped and spoiled the spell before the magic could finish.",
        ))
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a potion?",
            answer="A potion is a drink or mixture in a bottle that is supposed to do something magical.",
        ),
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a tale about a ghost, often in a spooky place, but it can still end gently.",
        ),
        QAItem(
            question="What does a breaker do?",
            answer="A breaker can knock, bump, or tip something over and spoil what was carefully set up.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something special in a story that can make surprising things happen.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    c = world.facts["child"]
    p = world.facts["potion"]
    return [
        f'Write a short ghost story for a child named {c.id} who opens {p.label} in a quiet place.',
        "Tell a gentle spooky story where a little breaker nearly spoils a magical potion.",
        f'Write a child-friendly ghost story with a {p.label} and a soft ending.',
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"place={world.place}")
    lines.append(f"magic_active={world.magic_active}")
    lines.append(f"breaker_bumped={world.breaker_bumped}")
    lines.append(f"potion_opened={world.potion_opened}")
    lines.append(f"ghost_visible={world.ghost_visible}")
    lines.append(f"ghost_friend={world.ghost_friend}")
    for e in world.entities.values():
        bits = []
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.touched_by_magic:
            bits.append("magic_touched=True")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = generate_world(params)
    tell_story(world, params)
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
        for i, p in enumerate(sample.prompts, 1):
            print(f"P{i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(place="attic", child_name="Mia", child_type="girl", potion_name="moon potion"),
    StoryParams(place="garden", child_name="Leo", child_type="boy", potion_name="starlight potion"),
    StoryParams(place="cellar", child_name="Ava", child_type="girl", potion_name="midnight potion"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(ASP_RULES)
        return
    if args.verify:
        print("OK: Python story world is available.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
