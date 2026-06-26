#!/usr/bin/env python3
"""
A small story world about a young superhero helping a nurse clean up an oily
biology-lab mishap through dialogue and a careful, brave rescue.
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
class Character:
    id: str
    role: str
    name: str
    kind: str = "character"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "she" if self.role in {"girl", "woman", "nurse"} else "he"

    def possessive(self) -> str:
        return "her" if self.role in {"girl", "woman", "nurse"} else "his"


@dataclass
class Location:
    name: str = "the biology wing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str
    sidekick_name: str
    nurse_name: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Character] = {}
        self.location = Location()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.dialogue_turns: list[tuple[str, str]] = []

    def add(self, ent: Character) -> Character:
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

    def copy(self) -> "World":
        import copy as _copy

        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.location = _copy.deepcopy(self.location)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.dialogue_turns = list(self.dialogue_turns)
        return w


ASP_RULES = r"""
#show risk/1.
#show fix/1.
risk(oil) :- spill(oil).
fix(oil) :- nurse(nina), hero(harper), tool(towel), tool(soap).
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("spill", "oil"),
        asp.fact("nurse", "nina"),
        asp.fact("hero", "harper"),
        asp.fact("tool", "towel"),
        asp.fact("tool", "soap"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero biology-lab story world with dialogue.")
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--sidekick-name", choices=SIDEKICK_NAMES)
    ap.add_argument("--nurse-name", choices=NURSE_NAMES)
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


HERO_NAMES = ["Nova", "Pulse", "Vector", "Spark", "Comet"]
SIDEKICK_NAMES = ["Milo", "Ruby", "Theo", "Iris", "Zane"]
NURSE_NAMES = ["Nina", "Mara", "June", "Tess", "Lena"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero_name or rng.choice(HERO_NAMES)
    sidekick = args.sidekick_name or rng.choice([n for n in SIDEKICK_NAMES if n != hero])
    nurse = args.nurse_name or rng.choice(NURSE_NAMES)
    return StoryParams(hero_name=hero, sidekick_name=sidekick, nurse_name=nurse)


def _setup_world(params: StoryParams) -> World:
    w = World()
    hero = w.add(Character(id="hero", role="hero", name=params.hero_name))
    sidekick = w.add(Character(id="sidekick", role="sidekick", name=params.sidekick_name))
    nurse = w.add(Character(id="nurse", role="nurse", name=params.nurse_name))
    w.facts.update(hero=hero, sidekick=sidekick, nurse=nurse)
    return w


def _predict_spill(world: World) -> bool:
    sim = world.copy()
    sim.location.meters["oil"] = 1
    return sim.location.meters["oil"] >= 1


def _dialogue(world: World, speaker: Character, line: str) -> None:
    world.dialogue_turns.append((speaker.name, line))
    world.say(f'"{line}" {speaker.name} said.')


def generate_story(world: World) -> None:
    hero: Character = world.facts["hero"]
    sidekick: Character = world.facts["sidekick"]
    nurse: Character = world.facts["nurse"]

    world.say(
        f"{hero.name} was a small superhero with a bright cape who loved the biology wing."
    )
    world.say(
        f"One afternoon, {nurse.name} was checking a tray of bottles when a slick oil bottle tipped."
    )
    world.say(
        f"{sidekick.name} gasped. The oil spread fast across the floor, shining like a dark puddle."
    )

    world.para()
    _dialogue(world, nurse, "Careful! That oil could make someone slip.")
    _dialogue(world, hero, "Don't worry. My team can help.")
    _dialogue(world, sidekick, "What should we do first?")
    _dialogue(world, nurse, "We need towels, a sealable jar, and a calm plan.")
    world.say(
        f"{hero.name} nodded. {hero.name} lifted the bottle upright while {sidekick.name} brought towels."
    )
    world.say(
        f"{nurse.name} pointed to the spill and said the biology tools had to stay clean."
    )

    world.para()
    if _predict_spill(world):
        world.location.meters["oil"] = 0
        world.say(
            f"{hero.name} pressed the towels around the spill, and {sidekick.name} handed over a dry jar."
        )
        _dialogue(world, hero, "I have it! The oil is soaked up.")
        _dialogue(world, nurse, "Excellent work, little hero. The lab is safe again.")
        world.say(
            f"At last, the floor shone clean, and {nurse.name} smiled at the brave pair."
        )
        world.say(
            f"{hero.name}'s cape fluttered as if it knew the mission was finished."
        )

    world.facts["resolved"] = True


def story_qa(world: World) -> list[QAItem]:
    hero: Character = world.facts["hero"]
    nurse: Character = world.facts["nurse"]
    sidekick: Character = world.facts["sidekick"]
    return [
        QAItem(
            question=f"Who was the young superhero in the story?",
            answer=f"The young superhero was {hero.name}.",
        ),
        QAItem(
            question=f"What problem happened in the biology wing?",
            answer="An oil bottle tipped over and made a slippery spill on the floor.",
        ),
        QAItem(
            question=f"Who helped keep the biology lab safe?",
            answer=f"{hero.name}, {sidekick.name}, and {nurse.name} worked together to keep the lab safe.",
        ),
        QAItem(
            question=f"What did the nurse ask for first?",
            answer="The nurse asked for towels, a sealable jar, and a calm plan.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why is oil slippery?",
            answer="Oil can make surfaces slippery because it spreads into a slick layer that is hard to stand on.",
        ),
        QAItem(
            question="What does a nurse do?",
            answer="A nurse helps people stay healthy, gives care, and keeps things safe in medical places.",
        ),
        QAItem(
            question="What is biology?",
            answer="Biology is the study of living things like plants, animals, and tiny cells.",
        ),
        QAItem(
            question="Why should a spill be cleaned quickly?",
            answer="A spill should be cleaned quickly so nobody slips and the area stays safe and tidy.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    hero: Character = world.facts["hero"]
    nurse: Character = world.facts["nurse"]
    return [
        f"Write a child-friendly superhero story about {hero.name} helping nurse {nurse.name} in a biology wing after an oil spill.",
        f"Tell a dialogue-heavy adventure where a brave hero and a nurse work together to clean up oil safely.",
        f"Create a short superhero tale with biology tools, a slippery oil spill, and kind dialogue.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        lines.append(f"  {ent.id}: name={ent.name} role={ent.role} meters={ent.meters} memes={ent.memes}")
    lines.append(f"  location: {world.location.name} meters={world.location.meters}")
    lines.append(f"  dialogue turns: {len(world.dialogue_turns)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== generation prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = _setup_world(params)
    generate_story(world)
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


CURATED = [
    StoryParams(hero_name="Nova", sidekick_name="Milo", nurse_name="Nina"),
    StoryParams(hero_name="Spark", sidekick_name="Ruby", nurse_name="Mara"),
    StoryParams(hero_name="Comet", sidekick_name="Theo", nurse_name="June"),
]


def asp_verify() -> int:
    import asp

    program = asp_program("#show risk/1.\n#show fix/1.")
    model = asp.one_model(program)
    atoms = asp.atoms(model, "risk")
    if ("oil",) in atoms:
        print("OK: ASP marks oil as a risk.")
        return 0
    print("MISMATCH: ASP did not mark oil as a risk.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show risk/1.\n#show fix/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show risk/1.\n#show fix/1."))
        print("risk:", asp.atoms(model, "risk"))
        print("fix:", asp.atoms(model, "fix"))
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
