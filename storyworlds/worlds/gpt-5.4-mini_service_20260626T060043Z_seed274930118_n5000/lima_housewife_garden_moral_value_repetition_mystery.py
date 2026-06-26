#!/usr/bin/env python3
"""
A small storyworld: a housewife, a garden, a lima bean mystery, and a gentle
ghost-story turn that resolves through patience, repetition, and kindness.

The seed image:
- A housewife tends a garden at dusk.
- A small mystery repeats: a pale lima bean keeps appearing where it should not.
- A soft ghostly presence seems to be trying to teach a moral value.
- The answer is found by repeating a kind action until the pattern makes sense.
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


# ---------------------------------------------------------------------------
# Core model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "housewife"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Garden:
    name: str = "the garden"
    twilight: bool = True
    wet: bool = False
    blooms: int = 3
    stillness: float = 0.0


@dataclass
class StoryParams:
    name: str = "Mabel"
    seed: Optional[int] = None


class World:
    def __init__(self, garden: Garden) -> None:
        self.garden = garden
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


def encode_mystery(world: World, hero: Entity, ghost: Entity, lima: Entity) -> None:
    hero.memes["curiosity"] = 1.0
    ghost.memes["mystery"] = 1.0
    lima.meters["appeared"] = 1.0
    world.facts["mystery"] = "the lima bean keeps appearing"
    world.say(
        f"{hero.id} was a housewife who loved {world.garden.name} when the air turned quiet."
    )
    world.say(
        f"At dusk, a single lima bean appeared on the stone path, pale as moonlight."
    )
    world.say(
        f"{hero.id} frowned, because the little bean was not where she had left it."
    )


def repeat_clue(world: World, hero: Entity, ghost: Entity, lima: Entity) -> None:
    world.para()
    hero.memes["worry"] = 1.0
    ghost.memes["signaling"] = 1.0
    world.say(
        f"The next evening, the lima bean appeared again beside the rosebush."
    )
    world.say(
        f"{hero.id} cleaned the path, watered the beans, and looked in the same spot again."
    )
    world.say(
        f"Each time she checked, the garden seemed to whisper the same soft question."
    )
    world.facts["repetition"] = "the bean reappears in different places"
    world.facts["clues"] = [
        "the bean is always near something that needs care",
        "the garden grows calmer after kind work",
    ]


def solve_mystery(world: World, hero: Entity, ghost: Entity, lima: Entity) -> None:
    world.para()
    hero.memes["understanding"] = 1.0
    ghost.memes["peace"] = 1.0
    world.say(
        f"On the third evening, {hero.id} found the lima bean beside the broken watering can."
    )
    world.say(
        f"She remembered the old note in the shed: 'Kindness returns when it is repeated.'"
    )
    world.say(
        f"So she mended the can, set out fresh water, and tucked the lima bean into the seed dish."
    )
    world.say(
        f"Then the little ghost in the garden smiled like a candle behind frosted glass."
    )
    world.say(
        f"The mystery was not a trick at all; it was a lesson to notice needs and help twice, then again."
    )
    world.say(
        f"After that, the garden felt warm, and no lima bean ever wandered alone."
    )
    world.facts["moral"] = "repeated kindness solves what fear cannot"
    world.facts["resolved"] = True


def tell(params: StoryParams) -> World:
    world = World(Garden())
    hero = world.add(Entity(id=params.name, kind="character", type="housewife", label="housewife"))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="little ghost"))
    lima = world.add(Entity(id="lima", kind="thing", type="bean", label="lima bean", phrase="a pale lima bean"))

    world.facts.update(hero=hero, ghost=ghost, lima=lima)

    world.say(
        f"{hero.id} lived beside {world.garden.name}, where the roses bowed in the evening breeze."
    )
    world.say(
        f"She was used to quiet chores, but she was not used to a mystery."
    )
    encode_mystery(world, hero, ghost, lima)
    repeat_clue(world, hero, ghost, lima)
    solve_mystery(world, hero, ghost, lima)
    return world


# ---------------------------------------------------------------------------
# ASP twin and reasonableness gate
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A mystery is reasonable if there is repetition and a moral resolution.
mystery_ok :- clue(repeats), clue(needs_care), moral(kindness_solves), setting(garden).

#show mystery_ok/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "garden"),
        asp.fact("clue", "repeats"),
        asp.fact("clue", "needs_care"),
        asp.fact("moral", "kindness_solves"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery_ok/0."))
    got = any(sym.name == "mystery_ok" for sym in model)
    expected = True
    if got == expected:
        print("OK: ASP and Python agree on the mystery structure.")
        return 0
    print("MISMATCH: ASP and Python disagree.")
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a gentle ghost story about {hero.id}, a housewife in a garden, and a lima bean mystery that repeats.",
        "Tell a child-facing story where repeated clues lead to a kind moral lesson.",
        "Write a soft spooky tale in which a garden ghost helps someone solve a mystery with patience.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a housewife who lived beside the garden and faced a small mystery.",
        ),
        QAItem(
            question="What kept appearing in the garden?",
            answer="A pale lima bean kept appearing in different places around the garden.",
        ),
        QAItem(
            question="How was the mystery solved?",
            answer="It was solved by repeating kind actions, fixing the broken watering can, and noticing the pattern.",
        ),
        QAItem(
            question="What moral value did the story show?",
            answer="The story showed that repeated kindness and patient care can solve a mystery.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a garden?",
            answer="A garden is a place where plants, flowers, and vegetables are grown and cared for.",
        ),
        QAItem(
            question="What is a lima bean?",
            answer="A lima bean is a kind of bean, which is a seed people can grow and eat.",
        ),
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a tale with a spooky feeling, often at night or in a quiet place, but it does not have to be truly scary.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world: a housewife, a garden, and a repeating lima bean mystery.")
    ap.add_argument("--name", choices=["Mabel", "Ruth", "Ivy", "Nora", "Hazel"])
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
    name = args.name or rng.choice(["Mabel", "Ruth", "Ivy", "Nora", "Hazel"])
    return StoryParams(name=name)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes}")
    lines.append(f"  garden: wet={world.garden.wet}, blooms={world.garden.blooms}, stillness={world.garden.stillness}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mystery_ok/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show mystery_ok/0."))
        print("mystery_ok" if any(sym.name == "mystery_ok" for sym in model) else "not_ok")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [StoryParams(name=n) for n in ["Mabel", "Ruth", "Ivy", "Nora", "Hazel"]]
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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
