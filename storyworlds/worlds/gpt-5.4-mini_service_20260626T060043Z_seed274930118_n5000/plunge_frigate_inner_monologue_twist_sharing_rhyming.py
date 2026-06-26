#!/usr/bin/env python3
"""
A tiny storyworld for a rhyming tale about a frigate, a plunge, a twist, and sharing.

Premise:
- A small crew sails a bright frigate.
- The hero wants to make a daring plunge into the sparkling harbor.
- A twist reveals the best prize is something to share, not keep.
- Inner monologue is used to show the hero thinking.
- The ending proves the change through a shared action.
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
class StoryParams:
    hero: str = "Milo"
    companion: str = "Nia"
    vessel: str = "the frigate"
    place: str = "the harbor"
    prize: str = "a silver shell"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    hero: Entity
    companion: Entity
    vessel: Entity
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


HERO_NAMES = ["Milo", "Tia", "Pip", "Rory", "Lina", "Jude"]
COMPANION_NAMES = ["Nia", "Pax", "June", "Sora", "Bea", "Kai"]
PRIZES = [
    "a silver shell",
    "a shiny star map",
    "a pearl ribbon",
    "a small gold bell",
]
PLACES = ["the harbor", "the quiet bay", "the moonlit dock"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A rhyming storyworld with a frigate, a plunge, a twist, and sharing."
    )
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--companion", choices=COMPANION_NAMES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--prize", choices=PRIZES)
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
    hero = args.hero or rng.choice(HERO_NAMES)
    companion = args.companion or rng.choice([n for n in COMPANION_NAMES if n != hero])
    place = args.place or rng.choice(PLACES)
    prize = args.prize or rng.choice(PRIZES)
    if hero == companion:
        raise StoryError("The hero and companion must be different characters.")
    return StoryParams(
        hero=hero,
        companion=companion,
        vessel="the frigate",
        place=place,
        prize=prize,
    )


def rhyming_intro(hero: str, vessel: str) -> str:
    return f"{hero} was aboard {vessel}, light as a song, where breezes were playful and days felt long."


def rhyming_setup(place: str, prize: str) -> str:
    return f"At {place}, a bright little treasure shone near the rope, and it made the crew beam with hope."


def inner_monologue(hero: Entity, prize: str) -> str:
    return (
        f"{hero.name} thought, 'Should I plunge right now and splash with a cheer, "
        f"or keep my paws dry and stay safe here?'"
    )


def twist_line(companion: Entity, prize: str) -> str:
    return (
        f"Then a twist came quick: {companion.name} laughed and said the prize was not mine alone to clutch, "
        f"for treasures feel better when shared so much."
    )


def resolve_line(hero: Entity, companion: Entity, prize: str) -> str:
    return (
        f"So {hero.name} chose sharing, with a grin and a spin; they split {prize} in half, and both gave a win."
    )


def build_world(params: StoryParams) -> World:
    hero = Entity(params.hero, "hero")
    companion = Entity(params.companion, "companion")
    vessel = Entity(params.vessel, "vessel")
    return World(params=params, hero=hero, companion=companion, vessel=vessel)


def simulate(world: World) -> None:
    p = world.params
    h = world.hero
    c = world.companion

    h.memes["curiosity"] = 1.0
    h.memes["want_plunge"] = 1.0
    world.facts["prize"] = p.prize
    world.facts["place"] = p.place
    world.facts["vessel"] = p.vessel

    world.say(rhyming_intro(h.name, p.vessel))
    world.say(rhyming_setup(p.place, p.prize))
    world.para()

    world.say(f"{h.name} wanted a plunge from the plank to the blue, but first came a thought: 'What should I do?'")
    world.say(inner_monologue(h, p.prize))
    h.memes["hesitation"] = 1.0

    world.para()
    world.say(f"At that very moment, {c.name} arrived with a smile so bright.")
    world.say(twist_line(c, p.prize))
    c.memes["sharing"] = 1.0
    h.memes["surprise"] = 1.0
    h.memes["sharing"] = 1.0
    world.facts["twist"] = True

    world.para()
    world.say(resolve_line(h, c, p.prize))
    world.say(
        f"Then both of them laughed on the frigate deck, while the sea swished soft and the sunset went west."
    )
    world.facts["resolved"] = True
    world.facts["shared"] = True


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    prompts = [
        f"Write a short rhyming story about {params.hero} on a frigate who thinks about a plunge.",
        f"Tell a gentle tale where {params.hero} meets a twist and learns sharing.",
        f"Make a child-friendly rhyming story featuring a frigate, a prize, and a shared ending.",
    ]
    story_qa = [
        QAItem(
            question=f"Who wanted to make the plunge on the frigate?",
            answer=f"{params.hero} wanted to make the plunge on the frigate.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {params.companion} said the prize should be shared, not kept alone.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {params.hero} and {params.companion} sharing {params.prize} and feeling happy together.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a frigate?",
            answer="A frigate is a sailing ship that can carry a crew across the water.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else enjoy something with you instead of keeping it all to yourself.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what the characters thought would happen.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in [world.hero, world.companion, world.vessel]:
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"  {ent.name:10} ({ent.kind:9}) meters={meters} memes={memes}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/1.
valid(story).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([asp.fact("domain", "frigate"), asp.fact("feature", "inner_monologue"), asp.fact("feature", "twist"), asp.fact("feature", "sharing")])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/1."))
    if asp.atoms(model, "valid") == [("story",)]:
        print("OK: ASP twin is consistent.")
        return 0
    print("MISMATCH: ASP twin failed.")
    return 1


CURATED = [
    StoryParams(hero="Milo", companion="Nia", place="the harbor", prize="a silver shell"),
    StoryParams(hero="Tia", companion="Pax", place="the quiet bay", prize="a shiny star map"),
    StoryParams(hero="Rory", companion="June", place="the moonlit dock", prize="a pearl ribbon"),
]


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
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/1."))
        print(asp.atoms(model, "valid"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
