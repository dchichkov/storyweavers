#!/usr/bin/env python3
"""
Storyworld: stern_demolish_cautionary_animal_story

A small animal-story world about a stern warning, a risky demolition, and a
cautious better choice.
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
class Creature:
    id: str
    species: str
    name: str
    role: str
    home: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: {"risk": 0.0, "damage": 0.0, "caution": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"worry": 0.0, "relief": 0.0, "pride": 0.0})

    def pronoun(self) -> str:
        return "they"

    def possessive(self) -> str:
        return "their"


@dataclass
class Thing:
    id: str
    label: str
    kind: str
    owner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: {"risk": 0.0, "damage": 0.0, "caution": 0.0})


@dataclass
class StoryParams:
    species: str
    hero_name: str
    elder_name: str
    home: str
    risky_thing: str
    safer_fix: str
    seed: Optional[int] = None


SPECIES = {
    "beaver": {
        "homes": ["riverbank lodge", "pond home"],
        "risky_thing": "old dam",
        "safer_fix": "fresh reeds",
        "actions": ("demolish", "build"),
    },
    "rabbit": {
        "homes": ["burrow tunnel", "meadow den"],
        "risky_thing": "thorny fence",
        "safer_fix": "soft grass path",
        "actions": ("demolish", "tidy"),
    },
    "fox": {
        "homes": ["hill den", "wood edge hollow"],
        "risky_thing": "rickety fence",
        "safer_fix": "quiet path",
        "actions": ("demolish", "repair"),
    },
}

HERO_NAMES = {
    "beaver": ["Milo", "Nina", "Pip", "Tara"],
    "rabbit": ["Mimi", "Luna", "Ollie", "Benny"],
    "fox": ["Ruby", "Fenn", "Sage", "Kiko"],
}

ELDER_NAMES = {
    "beaver": ["Bramble", "Hazel", "Wren"],
    "rabbit": ["Moss", "Fern", "Daisy"],
    "fox": ["Bracken", "Iris", "Rowan"],
}


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.creatures: dict[str, Creature] = {}
        self.things: dict[str, Thing] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        chunk: list[str] = []
        for line in self.lines:
            if line == "":
                if chunk:
                    out.append(" ".join(chunk))
                    chunk = []
            else:
                chunk.append(line)
        if chunk:
            out.append(" ".join(chunk))
        return "\n\n".join(out)


def build_world(params: StoryParams) -> World:
    world = World(params)
    hero = Creature("hero", params.species, params.hero_name, "young", params.home, ["curious", "stubborn"])
    elder = Creature("elder", params.species, params.elder_name, "stern elder", params.home, ["stern", "careful"])
    thing = Thing("thing", params.risky_thing, "risky")
    fix = Thing("fix", params.safer_fix, "safer")

    world.creatures[hero.id] = hero
    world.creatures[elder.id] = elder
    world.things[thing.id] = thing
    world.things[fix.id] = fix

    # Setup
    world.say(f"{hero.name} was a little {params.species} who loved to poke around {params.home}.")
    world.say(f"One day, {hero.name} noticed {params.risky_thing} and thought it looked ready to {SPECIES[params.species]['actions'][0]}.")
    world.say(f"{params.elder_name} was a stern elder who watched closely and kept the little ones safe.")
    world.para()

    # Tension
    hero.meters["risk"] += 1
    world.say(f"{hero.name} wanted to {SPECIES[params.species]['actions'][0]} it anyway, even though the stones wobbled and the sticks creaked.")
    world.say(f"{params.elder_name} gave a stern warning: \"Do not {SPECIES[params.species]['actions'][0]} that without a plan.\"")
    hero.memes["worry"] += 1
    elder.memes["worry"] += 1
    world.para()

    # Turn
    world.say(f"{hero.name} paused and looked again.")
    world.say(f"Instead of rushing in, {hero.name} fetched {params.safer_fix} and called for help.")
    hero.meters["caution"] += 1
    elder.meters["caution"] += 1
    world.say(f"Together, they chose the careful way: they kept the dangerous part steady and moved only what was loose.")
    world.para()

    # Resolution
    thing.meters["damage"] = 0.0
    fix.meters["caution"] += 1
    hero.memes["relief"] += 1
    elder.memes["pride"] += 1
    world.say(f"The risky pile stayed mostly in place, and nobody got hurt.")
    world.say(f"{hero.name} learned that a stern warning can be a kind gift when it stops a bad mistake.")
    world.say(f"At the end, {hero.name} stood beside {params.elder_name}, proud of choosing caution before demolition.")

    world.facts.update(
        hero=hero,
        elder=elder,
        thing=thing,
        fix=fix,
        action=SPECIES[params.species]["actions"][0],
        safer_action="choose caution",
        home=params.home,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Creature = f["hero"]
    elder: Creature = f["elder"]
    thing: Thing = f["thing"]
    return [
        f'Write a short animal story for young children about {hero.name}, {elder.name}, and a stern warning.',
        f"Tell a cautionary story where a little {hero.species} wants to demolish {thing.label} but learns to be careful.",
        f"Write an animal story with a gentle lesson: listen when a stern elder says something is too risky.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Creature = f["hero"]
    elder: Creature = f["elder"]
    thing: Thing = f["thing"]
    action = f["action"]
    return [
        QAItem(
            question=f"Who wanted to {action} the {thing.label}?",
            answer=f"{hero.name}, the young {hero.species}, wanted to {action} the {thing.label}.",
        ),
        QAItem(
            question=f"Who gave the stern warning?",
            answer=f"{elder.name} gave the stern warning and told {hero.name} not to rush.",
        ),
        QAItem(
            question="What did they do instead of making the situation worse?",
            answer=f"They chose caution, got help, and used a safer plan instead of a careless demolition.",
        ),
        QAItem(
            question=f"Why was the story cautionary?",
            answer=f"It was cautionary because {hero.name} learned that a risky choice could cause harm, so it was better to listen first.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does stern mean?",
            answer="Stern means serious and firm, like a grown-up who is warning you clearly because safety matters.",
        ),
        QAItem(
            question="What does demolish mean?",
            answer="Demolish means to tear something down or break it apart, usually carefully and with a plan.",
        ),
        QAItem(
            question="What is caution?",
            answer="Caution is careful behavior that helps keep people safe and avoids unnecessary trouble.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for c in world.creatures.values():
        lines.append(f"{c.id}: species={c.species} meters={dict(c.meters)} memes={dict(c.memes)}")
    for t in world.things.values():
        lines.append(f"{t.id}: label={t.label} kind={t.kind} meters={dict(t.meters)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is cautionary when a risky demolition is prevented by caution.
cautionary_story(S) :- stern_warning(S), risky_demolish(S), choose_caution(S).

stern_warning(S) :- story(S), elder_stern(S).
risky_demolish(S) :- story(S), wants_demolish(S), unsafe(S).
choose_caution(S) :- story(S), safer_choice(S).
"""


def asp_facts(params: StoryParams) -> str:
    import asp
    lines = [
        asp.fact("story", "s1"),
        asp.fact("elder_stern", "s1"),
        asp.fact("wants_demolish", "s1"),
        asp.fact("unsafe", "s1"),
        asp.fact("safer_choice", "s1"),
    ]
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts(StoryParams('beaver', 'Milo', 'Bramble', 'riverbank lodge', 'old dam', 'fresh reeds'))}\n{ASP_RULES}\n#show cautionary_story/1.\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = set(asp.atoms(model, "cautionary_story"))
    if atoms == {("s1",)}:
        print("OK: ASP gate matches the cautionary pattern.")
        return 0
    print("MISMATCH: ASP did not recognize the cautionary story.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about stern caution and risky demolition.")
    ap.add_argument("--species", choices=sorted(SPECIES))
    ap.add_argument("--hero-name")
    ap.add_argument("--elder-name")
    ap.add_argument("--home")
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
    species = args.species or rng.choice(sorted(SPECIES))
    cfg = SPECIES[species]
    home = args.home or rng.choice(cfg["homes"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES[species])
    elder_name = args.elder_name or rng.choice(ELDER_NAMES[species])
    return StoryParams(
        species=species,
        hero_name=hero_name,
        elder_name=elder_name,
        home=home,
        risky_thing=cfg["risky_thing"],
        safer_fix=cfg["safer_fix"],
    )


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


CURATED = [
    StoryParams("beaver", "Milo", "Bramble", "riverbank lodge", "old dam", "fresh reeds"),
    StoryParams("rabbit", "Mimi", "Moss", "meadow den", "thorny fence", "soft grass path"),
    StoryParams("fox", "Ruby", "Bracken", "hill den", "rickety fence", "quiet path"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
