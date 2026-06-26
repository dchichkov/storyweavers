#!/usr/bin/env python3
"""
A tiny storyworld about rent, lime, and mortgage, told in a nursery-rhyme style
with inner monologue as the main narrative instrument.

A short source tale behind the world:
---
Mina lived in a snug little house with a green door and a windowsill full of
limes. Each month, she had to pay the rent. Her mama kept a careful budget and
also talked about the mortgage on the house. One week, the rent was due and the
lime basket was empty after Mina shared the last fruit with her neighbors.

Mina worried in her head. If she spent all the coins on candy, there would not
be enough for rent. If the mortgage was late, the grown-ups would sigh. Then
Mina remembered she could help by making lime water at the market stall and
pocketing a few honest coins. She counted, sold, paid, and the house stayed
warm, bright, and safe.
---
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
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"coins": 0.0, "stress": 0.0, "joy": 0.0, "hunger": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "hope": 0.0, "care": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "she", "object": "her", "possessive": "her"}[case]


@dataclass
class Setting:
    place: str = "a snug little house"
    neighborhood: str = "a quiet lane"
    has_limes: bool = True


@dataclass
class StoryParams:
    name: str = "Mina"
    helper: str = "Mama"
    setting: str = "house"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def para(self) -> None:
        if self.lines and not self.lines[-1].endswith("\n\n"):
            self.lines.append("\n\n")


def nursery_rhyme(text: str) -> str:
    return text


def inner_voice(text: str) -> str:
    return f"({text})"


def build_world(params: StoryParams) -> World:
    world = World(Setting())
    hero = world.add(Entity(id=params.name, kind="character", label=params.name, role="child"))
    helper = world.add(Entity(id=params.helper, kind="character", label=params.helper, role="parent"))
    rent = world.add(Entity(id="rent", label="rent", phrase="the monthly rent", role="bill"))
    lime = world.add(Entity(id="lime", label="lime", phrase="a bowl of bright limes", role="fruit"))
    mortgage = world.add(Entity(id="mortgage", label="mortgage", phrase="the house mortgage", role="bill"))

    hero.meters["coins"] = 3
    helper.meters["coins"] = 7
    rent.meters["coins"] = 5
    mortgage.meters["coins"] = 6
    lime.meters["joy"] = 1

    world.facts.update(hero=hero, helper=helper, rent=rent, lime=lime, mortgage=mortgage)
    return world


def tell(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    rent = world.facts["rent"]
    lime = world.facts["lime"]
    mortgage = world.facts["mortgage"]

    world.say(nursery_rhyme(
        f"On a neat little lane in a snug little house, lived {hero.id}, quiet as a mouse."
    ))
    world.say(nursery_rhyme(
        f"On the sill sat {lime.phrase}, green as the grass after morning rain."
    ))
    world.say(inner_voice(
        f"I must be careful, {hero.id} thought. The rent comes first, and the mortgage too."
    ))
    world.say(nursery_rhyme(
        f"One bright day, {helper.id} said, 'The rent is due; let us count the coins.'"
    ))
    hero.memes["worry"] += 1
    hero.meters["stress"] += 1
    world.say(inner_voice(
        f"If I buy sweet cake now, there will not be enough for rent. That would be a plain old pain."
    ))
    world.say(nursery_rhyme(
        f"{hero.id} looked at the empty basket and felt the worry start to bloom."
    ))
    world.say(inner_voice(
        f"I can help, I can mend this. I can make lime water and earn a little more."
    ))
    world.say(nursery_rhyme(
        f"So {hero.id} carried the limes to the market stall and squeezed each one with care."
    ))
    hero.meters["coins"] += 5
    helper.meters["coins"] += 5
    rent.meters["coins"] += 5
    mortgage.meters["coins"] += 6
    hero.memes["hope"] += 2
    hero.memes["worry"] = 0
    hero.meters["stress"] = 0
    lime.meters["joy"] += 1
    world.say(nursery_rhyme(
        f"Coins went clink in a tidy little tune, and the rent was paid by noon."
    ))
    world.say(nursery_rhyme(
        f"{helper.id} smiled wide and said the mortgage would be on time."
    ))
    world.say(inner_voice(
        f"Now the house is safe, and my heart is light. A careful thought can save the day."
    ))
    world.say(nursery_rhyme(
        f"That night the snug little house stayed warm and bright, and the limes shone green in the moonlight."
    ))


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a nursery-rhyme style story about rent, lime, and mortgage, with a child thinking quietly inside.',
        f"Tell a gentle story where {world.facts['hero'].id} worries about rent and helps the family in a small, honest way.",
        "Write a simple tale with a snug house, a bowl of limes, and a mortgage that must be paid on time.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    rent = world.facts["rent"]
    mortgage = world.facts["mortgage"]
    lime = world.facts["lime"]
    return [
        QAItem(
            question=f"Why did {hero.id} feel worried when the rent was due?",
            answer=f"{hero.id} worried because the rent had to be paid, and {hero.id} did not want the house bill to fall behind."
        ),
        QAItem(
            question=f"What did {hero.id} do to help {helper.id} with the rent and mortgage?",
            answer=f"{hero.id} took the limes to the market, made a little honest money, and helped pay the rent and mortgage on time."
        ),
        QAItem(
            question=f"What stayed green and bright at the end of the story?",
            answer=f"The limes stayed green and bright, and the snug little house stayed safe and warm."
        ),
        QAItem(
            question=f"How did {hero.id} feel after the money was counted?",
            answer=f"{hero.id} felt hopeful and relieved because the rent was paid and the mortgage was kept on schedule."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is rent?",
            answer="Rent is money paid regularly to live in a house or apartment."
        ),
        QAItem(
            question="What is a mortgage?",
            answer="A mortgage is a loan used to buy a house, usually paid back a little at a time."
        ),
        QAItem(
            question="What is a lime?",
            answer="A lime is a small green citrus fruit with a sharp, tangy taste."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about rent, lime, and mortgage.")
    ap.add_argument("--name", default="Mina")
    ap.add_argument("--helper", default="Mama")
    ap.add_argument("--setting", default="house")
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
    return StoryParams(
        name=args.name or rng.choice(["Mina", "Lina", "Tia", "Nora"]),
        helper=args.helper or rng.choice(["Mama", "Papa", "Grandma"]),
        setting=args.setting or "house",
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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


ASP_RULES = r"""
#show story_ready/0.
story_ready :- rent, lime, mortgage.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("rent"),
        asp.fact("lime"),
        asp.fact("mortgage"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show story_ready/0."))
    ok = any(sym.name == "story_ready" for sym in model)
    if ok:
        print("OK: ASP gate sees the rent/lime/mortgage world.")
        return 0
    print("MISMATCH: ASP gate failed.")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show story_ready/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(resolve_params(args, random.Random(base_seed + i))) for i in range(3)]
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
