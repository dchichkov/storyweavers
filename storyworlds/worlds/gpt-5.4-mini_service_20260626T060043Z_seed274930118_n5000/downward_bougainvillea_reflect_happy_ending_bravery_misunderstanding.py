#!/usr/bin/env python3
"""
A small standalone storyworld for a fable-like garden tale about a downward
bougainvillea, a misunderstanding, and a brave act that leads to a happy ending.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    detail: str


@dataclass
class StoryParams:
    place: str = "garden"
    hero_name: str = "Mina"
    hero_type: str = "girl"
    neighbor_name: str = "Elder Reed"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PLACES = {
    "garden": Place(
        name="the garden",
        detail="The garden sat below a stone wall, and a bougainvillea spilled downward in bright pink curtains.",
    ),
    "courtyard": Place(
        name="the courtyard",
        detail="The courtyard was quiet, with a bougainvillea draped downward from a balcony like a ribbon.",
    ),
}

NAMES = ["Mina", "Tavi", "Lena", "Pip", "Arin", "Milo"]
NEIGHBORS = ["Elder Reed", "Aunt Sora", "Old Bram", "Mrs. Vale"]
TRAITS = ["gentle", "curious", "careful", "spirited"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like garden storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--neighbor")
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
    return StoryParams(
        place=args.place or rng.choice(list(PLACES)),
        hero_name=args.name or rng.choice(NAMES),
        hero_type="girl",
        neighbor_name=args.neighbor or rng.choice(NEIGHBORS),
        seed=args.seed,
    )


@dataclass
class StoryModel:
    hero: Entity
    neighbor: Entity
    vine: Entity
    lantern: Entity
    misunderstanding: bool = False
    brave: bool = False
    reflected: bool = False


def _narrate_intro(world: World, model: StoryModel) -> None:
    world.say(
        f"{model.hero.id} lived near {world.place.name}, where {world.place.detail}"
    )
    world.say(
        f"Every morning, {model.hero.id} liked to watch the bougainvillea and think about how beauty can grow downward and still reach the light."
    )


def _narrate_inciting(world: World, model: StoryModel) -> None:
    world.para()
    world.say(
        f"One afternoon, {model.hero.id} noticed {model.neighbor.id} frowning at the hanging flowers."
    )
    world.say(
        f"When {model.hero.id} moved the lantern closer, the old neighbor thought {model.hero.pronoun('subject')} was tampering with the vine."
    )
    model.misunderstanding = True
    model.neighbor.memes["worry"] = 1.0
    model.hero.memes["hurt"] = 1.0


def _narrate_turn(world: World, model: StoryModel) -> None:
    world.para()
    model.hero.memes["bravery"] = 1.0
    model.brave = True
    world.say(
        f"Instead of hiding, {model.hero.id} took a careful breath and stepped closer."
    )
    world.say(
        f"{model.hero.id} showed {model.neighbor.id} that the lantern was not meant to hurt the plant; it was meant to reveal a tiny sparrow tangled in the bougainvillea's lower branches."
    )
    world.say(
        f"That was when {model.neighbor.id} understood the mistake and felt ashamed for judging too quickly."
    )
    model.neighbor.memes["shame"] = 1.0


def _narrate_resolution(world: World, model: StoryModel) -> None:
    world.para()
    model.reflected = True
    model.hero.memes["joy"] = 1.0
    model.neighbor.memes["gratitude"] = 1.0
    model.vine.meters["rescued"] = 1.0
    model.lantern.meters["lit"] = 1.0
    world.say(
        f"Together they freed the sparrow, and the bird flew up through the pink blossoms."
    )
    world.say(
        f"{model.neighbor.id} thanked {model.hero.id} for the bravery to speak kindly instead of running away."
    )
    world.say(
        f"At sunset, {model.hero.id} reflected that a happy ending often begins when someone chooses courage over silence."
    )


def generate_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    neighbor = world.add(Entity(id=params.neighbor_name, kind="character", type="elder"))
    vine = world.add(Entity(id="bougainvillea", type="plant", label="bougainvillea"))
    lantern = world.add(Entity(id="lantern", type="thing", label="lantern"))
    model = StoryModel(hero=hero, neighbor=neighbor, vine=vine, lantern=lantern)
    _narrate_intro(world, model)
    _narrate_inciting(world, model)
    _narrate_turn(world, model)
    _narrate_resolution(world, model)
    world.facts.update(
        hero=hero,
        neighbor=neighbor,
        vine=vine,
        lantern=lantern,
        misunderstanding=model.misunderstanding,
        brave=model.brave,
        reflected=model.reflected,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    neighbor = f["neighbor"]
    return [
        f"Write a short fable about {hero.id}, a downward bougainvillea, and a misunderstanding in {world.place.name}.",
        f"Tell a child-friendly story where {hero.id} is brave enough to correct {neighbor.id} kindly.",
        "Write a gentle garden fable that ends with someone reflecting on a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    neighbor = f["neighbor"]
    return [
        QAItem(
            question=f"Who was the brave character in the story?",
            answer=f"The brave character was {hero.id}, who spoke up kindly instead of hiding from the misunderstanding.",
        ),
        QAItem(
            question=f"What caused the misunderstanding?",
            answer=f"{neighbor.id} thought the lantern was being used to harm the bougainvillea, but it was really there to help find a trapped sparrow.",
        ),
        QAItem(
            question=f"What made the ending happy?",
            answer=f"The sparrow was freed, the mistake was cleared up, and everyone felt relieved and grateful by the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bougainvillea?",
            answer="Bougainvillea is a flowering vine with bright, colorful blossoms that can trail over walls and fences.",
        ),
        QAItem(
            question="What does it mean to reflect?",
            answer="To reflect means to think carefully about what happened and what it teaches you.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is the choice to do the right thing even when you feel nervous or afraid.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something is true, but they do not yet have the full story.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        out.append(f"{e.id}: {', '.join(parts) if parts else 'empty'}")
    out.append(f"facts: {sorted(world.facts.keys())}")
    return "\n".join(out)


ASP_RULES = r"""
% This world is intentionally simple: a brave correction resolves a misunderstanding.
misunderstanding :- seen_wrongly.
happy_ending :- misunderstanding, brave_act, clarify, gratitude.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("seen_wrongly"),
            asp.fact("brave_act"),
            asp.fact("clarify"),
            asp.fact("gratitude"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as err:  # pragma: no cover
        print(f"ASP unavailable: {err}")
        return 1
    model = asp.one_model(asp_program("#show happy_ending/0."))
    atoms = {str(a) for a in model}
    if "happy_ending" in atoms:
        print("OK: ASP reasoner confirms the happy ending.")
        return 0
    print("MISMATCH: ASP reasoner did not confirm the happy ending.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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
        print(asp_program("#show happy_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, place in enumerate(PLACES):
            params = StoryParams(
                place=place,
                hero_name=NAMES[i % len(NAMES)],
                neighbor_name=NEIGHBORS[i % len(NEIGHBORS)],
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
