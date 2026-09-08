#!/usr/bin/env python3
"""
A child-facing superhero storyworld about bacon, a surprising twist, and
reconciliation after a hasty choice.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass(frozen=True)
class Mission:
    id: str
    opening: str
    danger: str
    twist: str
    clue: str
    bacon_use: str
    careful_action: str
    result: str
    reconciliation: str
    ending: str


@dataclass
class StoryParams:
    hero: str
    partner: str
    mission: str
    trait: str
    seed: Optional[int] = None


MISSIONS = [
    Mission(
        "smoke_alarm",
        "At breakfast time, silver smoke curled over Brightbridge City.",
        "The alarm tower shouted that a kitchen fire was racing toward the market.",
        "The smoke was not from a fire at all; a mountain of bacon had burned in the mayor's giant pan.",
        "A tiny fan pushed the smoke in neat circles, while the windows stayed cool.",
        "the bacon's warm grease to loosen a jammed fan belt",
        "shared the work, opened the kitchen windows, and used the cooled grease carefully to free the belt",
        "the fan carried the smoke away before anyone was hurt",
        "the hero apologized for blaming the mayor and the mayor promised to ask for help before cooking another mountain of bacon",
        "By noon, Brightbridge smelled of fresh bread instead of smoke, and the hero and mayor ate bacon together.",
    ),
    Mission(
        "museum_robot",
        "The city museum's tiny robot began rolling in wild circles around the breakfast exhibit.",
        "Visitors feared it would crash into the glass case holding the town's first superhero cape.",
        "The robot was not attacking; a strip of bacon had slipped beneath its wheel and made its guiding sensor slippery.",
        "Its wheel squeaked only when it crossed the buttery display mat.",
        "a clean napkin and one crisp piece of bacon",
        "removed the bacon from the wheel, wiped the sensor, and asked the museum keeper to test the robot slowly",
        "the robot stopped spinning and guided visitors safely around the cape",
        "the hero admitted that a loud machine is not always a villain, while the keeper forgave the hurried accusation",
        "The robot gave one polite beep beside the cape, and everyone shared the last crisp piece of bacon.",
    ),
    Mission(
        "rooftop_signal",
        "A red signal blinked from the tallest rooftop during the town's pancake festival.",
        "The hero's partner believed a masked enemy had stolen the emergency beacon.",
        "The signal came from a friendly rescue drone whose bacon-shaped banner had covered its blue light.",
        "The banner fluttered only when the wind blew from the bakery roof.",
        "a soft cloth and a strip of bacon saved for the hungry drone pilot",
        "removed the banner from the light, checked the drone's controls, and shared the bacon with the tired pilot",
        "the beacon turned blue and guided lost festival children to their families",
        "the partner and hero reconciled after admitting they had both guessed too quickly",
        "Above the festival, the blue beacon shone while friends carried warm pancakes home.",
    ),
    Mission(
        "park_shadow",
        "A huge shadow stretched across the park just as children gathered for a hero lesson.",
        "The shadow looked like a monster reaching over the swings.",
        "It was only a parade balloon tangled in a tree, with a bacon-shaped tail making the frightening outline.",
        "The shadow moved opposite the balloon whenever the afternoon sun shifted.",
        "a rope, a ladder, and a small bacon sandwich for the hungry tree-climber",
        "kept the children back, removed the rope from the branch, and helped the tree-climber eat before trying again",
        "the balloon floated free without tearing the tree or frightening anyone",
        "the hero and partner made peace by thanking each other for the clues each had noticed",
        "The balloon bobbed like a pink moon, and the children cheered beneath its harmless shadow.",
    ),
]

HERO_NAMES = ["Luna", "Nova", "Pip", "Maya", "Jett"]
PARTNER_NAMES = ["Kai", "Rae", "Sol", "Tess", "Milo"]
TRAITS = ["brave", "patient", "curious", "kind", "careful"]

DIALOGUES = [
    "Wait. What did you notice before we decide?",
    "Could this trouble be asking us to look again?",
    "Let us help each other instead of guessing.",
    "What if the loudest clue is not the truest one?",
    "Can we remove the danger without blaming anyone?",
]


def meter(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def meme(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def add_meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = meter(entity, key) + amount


def add_meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = meme(entity, key) + amount


def valid_combos() -> list[tuple[str, str]]:
    return [(mission, "skyline") for mission in (m.id for m in MISSIONS)]


def reasonableness_gate(params: StoryParams) -> None:
    if params.mission not in {m.id for m in MISSIONS}:
        raise StoryError(f"Unknown mission: {params.mission}")
    if not params.hero.strip() or not params.partner.strip():
        raise StoryError("A superhero story needs both a hero and a partner.")
    if params.hero.strip().lower() == params.partner.strip().lower():
        raise StoryError("The hero and partner must have different names.")


def tell(world: World, params: StoryParams) -> None:
    mission = next(m for m in MISSIONS if m.id == params.mission)
    hero = world.add(Entity(params.hero, "character", "superhero", params.hero))
    partner = world.add(Entity(params.partner, "character", "partner", params.partner))
    bacon = world.add(Entity("bacon", "food", "bacon", "bacon"))
    hero.memes.update(curiosity=1.0, worry=1.0)
    partner.memes.update(trust=1.0)

    world.say(
        f"In Skyline City, {params.hero} was a {params.trait} young superhero who protected people with courage and good questions."
    )
    world.say(
        f"{params.partner} worked beside {params.hero}, and their rescue rule was simple: remove danger first, then understand it."
    )
    world.say(mission.opening)
    world.say(mission.danger)
    world.para()

    world.say(
        f"{params.hero} reached for the fastest answer, but {params.partner} pointed toward the trouble."
    )
    world.say(mission.twist)
    add_meme(hero, "surprise", 1.0)
    world.say(f'"{DIALOGUES[(params.seed or 0) % len(DIALOGUES)]}" said {params.hero}.')
    world.say(
        f"{params.partner} answered, 'I noticed this: {mission.clue}'"
    )
    add_meme(hero, "listening", 1.0)

    world.para()
    add_meter(hero, "cooperation", 1.0)
    add_meter(partner, "cooperation", 1.0)
    world.say(f"Together they used {mission.bacon_use}.")
    world.say(f"{params.hero} {mission.careful_action}.")
    add_meter(bacon, "shared", 1.0)
    add_meme(hero, "trust", 1.0)
    add_meme(partner, "trust", 1.0)
    world.say(f"The careful plan worked: {mission.result}.")
    world.para()

    add_meme(hero, "regret", 1.0)
    add_meme(partner, "forgiveness", 1.0)
    world.say(
        f"Afterward, {params.hero} said, 'I was wrong to rush and blame you.' {params.partner} replied, 'I should have explained what I saw sooner.'"
    )
    world.say(
        f"Their reconciliation began with honest words and continued through shared work: {mission.reconciliation}."
    )
    world.say(
        f"That was the twist {params.hero} remembered: a real superhero does not only remove danger; a real superhero also repairs trust."
    )
    world.say(mission.ending)

    world.facts.update(
        hero=hero,
        partner=partner,
        bacon=bacon,
        mission=mission,
        dialogue=DIALOGUES[(params.seed or 0) % len(DIALOGUES)],
    )


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = World("Skyline City")
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    mission: Mission = world.facts["mission"]
    hero: Entity = world.facts["hero"]
    return [
        f"Write a superhero story about {hero.label} protecting Skyline City when bacon causes a problem.",
        f"Tell a child-friendly story with a Twist: {mission.twist}",
        "Write a story with Reconciliation after two superhero friends misunderstand one another.",
    ]


def story_qa(world: World) -> list[QAItem]:
    mission: Mission = world.facts["mission"]
    hero: Entity = world.facts["hero"]
    partner: Entity = world.facts["partner"]
    return [
        QAItem(
            f"What danger did {hero.label} and {partner.label} face?",
            f"They faced this danger: {mission.danger}",
        ),
        QAItem(
            "What was the twist?",
            f"The twist was that {mission.twist}",
        ),
        QAItem(
            f"What clue did {partner.label} notice?",
            f"{partner.label} noticed that {mission.clue}",
        ),
        QAItem(
            "How did bacon help?",
            f"They used {mission.bacon_use}.",
        ),
        QAItem(
            "How was the danger removed?",
            f"{hero.label} {mission.careful_action}, and {mission.result}.",
        ),
        QAItem(
            "How did the superheroes reconcile?",
            f"They apologized, listened to each other, and learned that {mission.reconciliation}.",
        ),
        QAItem(
            "What did the hero learn?",
            "The hero learned that courage includes slowing down, sharing credit, and repairing trust after a mistake.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a superhero?",
            "A superhero is a brave helper who uses special abilities, training, or cleverness to protect others.",
        ),
        QAItem(
            "What is reconciliation?",
            "Reconciliation is making peace after a disagreement by telling the truth, listening, apologizing, and working together again.",
        ),
        QAItem(
            "Why should someone remove a danger carefully?",
            "A danger should be removed carefully so the solution does not hurt people, animals, or useful things nearby.",
        ),
        QAItem(
            "What is a twist in a story?",
            "A twist is a surprising change in what the characters or readers thought was happening.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---", f"place: {world.place}"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.label}: meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
valid(Mission, skyline) :- mission(Mission).
mission(smoke_alarm).
mission(museum_robot).
mission(rooftop_signal).
mission(park_shadow).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [asp.fact("setting", "skyline")]
        + [asp.fact("mission", mission.id) for mission in MISSIONS]
    )


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(asp.one_model(asp_program()), "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py != clingo:
        print(f"MISMATCH: Python={sorted(py)} ASP={sorted(clingo)}")
        return 1
    for params in curated_params():
        generate(params)
    print(f"OK: ASP matches Python ({len(py)} combinations); stories exercised.")
    return 0


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def curated_params() -> list[StoryParams]:
    return [
        StoryParams("Luna", "Kai", "smoke_alarm", "brave", 11),
        StoryParams("Nova", "Rae", "museum_robot", "curious", 22),
        StoryParams("Pip", "Sol", "rooftop_signal", "kind", 33),
        StoryParams("Maya", "Tess", "park_shadow", "careful", 44),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a superhero story about bacon, a twist, and reconciliation."
    )
    parser.add_argument("--hero")
    parser.add_argument("--partner")
    parser.add_argument("--mission", choices=[m.id for m in MISSIONS])
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HERO_NAMES)
    partner = args.partner or rng.choice([n for n in PARTNER_NAMES if n != hero])
    mission = args.mission or rng.choice([m.id for m in MISSIONS])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(hero, partner, mission, trait)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp or args.asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in curated_params()]
    else:
        seen: set[str] = set()
        for index in range(max(args.n, 1)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
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

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.hero}: {sample.params.mission}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
