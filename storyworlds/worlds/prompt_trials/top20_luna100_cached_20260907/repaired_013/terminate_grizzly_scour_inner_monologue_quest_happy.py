#!/usr/bin/env python3
"""
A child-facing superhero quest about a grizzly bear, a dangerous signal,
and the brave choice to scour trouble away without hurting anyone.
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
class StoryParams:
    setting: str = "Brightwood City"
    hero: str = "Luna"
    companion: str = "Pip"
    grizzly: str = "Bruno"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.name] = entity
        return entity


SETTING_REGISTRY = {
    "Brightwood City": {"district": "the glowing park", "hazard": "a runaway storm beacon"},
    "Harbor Hill": {"district": "the windy lighthouse hill", "hazard": "a broken rescue siren"},
    "Maplebridge Town": {"district": "the old clock square", "hazard": "a humming power cart"},
}

HEROES = ["Luna", "Nova", "Sunny", "Rae"]
COMPANIONS = ["Pip", "Milo", "Tess", "Jun"]
GRIZZLIES = ["Bruno", "Moss", "Bram", "Honey"]


@dataclass(frozen=True)
class QuestArc:
    title: str
    trouble: str
    clue: str
    choice: str
    action: str
    rescue: str
    ending: str
    trouble_answer: str
    choice_answer: str
    rescue_answer: str


ARCS = [
    QuestArc(
        "The Grizzly and the Storm Beacon",
        "A storm beacon flashed wildly above the park, and its loud pulse made Bruno the grizzly panic.",
        "Luna noticed that Bruno was not chasing people; he was trying to protect a tiny cub hidden beneath a bench.",
        "She thought, \"I could terminate the beacon's signal at once, but I must not scare Bruno or leave the cub in the dark.\"",
        "Luna asked Pip to shine a soft lamp toward the cub while she climbed the tower and scoured the tangled vines from the beacon's switch.",
        "The beacon quieted, Bruno carried his cub to a safe grove, and the frightened crowd learned to stand still and speak gently.",
        "At sunrise, Bruno left a paw-shaped mark beside Luna's bright shield.",
        "The storm beacon's flashing noise frightened Bruno while he guarded his hidden cub.",
        "Luna chose to stop the signal carefully, protect the cub, and avoid frightening the grizzly.",
        "She removed the vines, quieted the beacon, and helped Bruno lead his cub to safety.",
    ),
    QuestArc(
        "The Grizzly's Golden Honey",
        "A golden honey cart rolled downhill toward a crowded bridge, while Bruno lumbered after it.",
        "Inside the cart was a jar of medicine honey that Bruno needed for a sore paw.",
        "Luna thought, \"I can terminate the cart's motion, but I should scour the bridge clear before I leap.\"",
        "She sent Pip to warn the walkers, then swept loose branches from the bridge and caught the cart with her moon-rope.",
        "The cart stopped safely, and Luna shared the medicine honey with Bruno after a vet checked his paw.",
        "That evening, Bruno rested beside a picnic blanket while children painted him a golden crown.",
        "A honey cart rolled toward a crowded bridge, and Bruno followed because his paw needed the medicine honey.",
        "Luna cleared the bridge and stopped the cart instead of rushing blindly into the crowd.",
        "The cart was stopped safely, and a vet used the honey to soothe Bruno's paw.",
    ),
    QuestArc(
        "The Grizzly Under the Stage",
        "A school festival had to begin, but Bruno was curled beneath the stage after a curtain rope wrapped around his leg.",
        "Luna heard his quiet growl and realized that the grizzly was hurt, not angry.",
        "She told herself, \"I must terminate the music, scour away the loose cords, and give Bruno time to trust us.\"",
        "Pip silenced the speakers while Luna used a silver beam to cut only the slack rope, leaving Bruno's fur untouched.",
        "Bruno stepped free, and the children changed their festival song into a gentle welcome tune.",
        "When the moon rose, Bruno tapped the rhythm with one enormous paw as everyone danced.",
        "Bruno was trapped and hurt beneath the festival stage by a curtain rope.",
        "Luna stopped the loud music, cleared the loose cords, and waited patiently rather than startling him.",
        "She freed Bruno without hurting his fur, and the festival became a gentle welcome for him.",
    ),
    QuestArc(
        "The Grizzly's Lost Star",
        "A small star-drone fell into the forest, and its bright alarm drew Bruno toward a deep ravine.",
        "Luna found the drone's map and saw that its flashing light was making Bruno walk the wrong way.",
        "She thought, \"To finish this quest, I must terminate the alarm and scour the trail for a safe crossing.\"",
        "With Pip holding a steady lantern, Luna cleaned branches from an old footpath and turned off the drone's alarm.",
        "Bruno followed the quiet path back to his den, while Luna repaired the drone and returned its star-light to the sky.",
        "The repaired star-drone blinked above the den, where Bruno and Luna watched it together.",
        "A fallen star-drone's alarm lured Bruno toward a dangerous ravine.",
        "Luna stopped the alarm and cleared a safe path instead of chasing Bruno toward the ravine.",
        "Bruno returned safely, and Luna repaired the drone so its light could guide travelers again.",
    ),
    QuestArc(
        "The Grizzly's Rainy Rescue",
        "Rain filled the town tunnel, and Bruno stood in the water because three ducklings were trapped on the far side.",
        "Luna saw that the grizzly was guarding the ducklings from the rushing drain.",
        "She whispered, \"I will terminate the drain's pull and scour a channel toward safety, one careful step at a time.\"",
        "Pip held an umbrella over the ducklings while Luna cleared mud from a side channel and shut the rusty drain gate.",
        "The water sank, the ducklings waddled out, and Bruno followed them to a warm shelter.",
        "After the rain, the ducklings slept in a basket while Bruno smiled beside a bowl of berries.",
        "Floodwater trapped three ducklings, and Bruno guarded them near a dangerous drain.",
        "Luna stopped the drain and cleared a safe channel while Pip protected the ducklings from the rain.",
        "The water fell, the ducklings escaped, and Bruno reached a warm shelter with them.",
    ),
]


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join((params.setting, params.hero, params.companion, params.grizzly))
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text))


def _fill(text: str, facts: dict[str, object]) -> str:
    return text.format(**facts)


def _start(text: str) -> str:
    return text[:1].upper() + text[1:]


def _story_lines(world: World) -> list[str]:
    facts = world.facts
    arc: QuestArc = facts["arc"]
    hero = facts["hero"]
    companion = facts["companion"]
    grizzly = facts["grizzly"]
    setting = facts["setting"]

    opening = [
        f"In {setting}, Luna wore a moon-bright cape and watched over every street.",
        f"At sunset in {setting}, {hero} began a new superhero quest with {companion}.",
        f"People in {setting} knew {hero} by the silver star on her shield.",
        f"The bell of {setting} rang three times when {hero} and {companion} saw trouble.",
    ][facts["variant"]]

    return [
        f"{opening} Today, {hero} was searching for a way to help everyone, even a frightened grizzly named {grizzly}.",
        f"\"What is happening?\" {companion} asked. {_start(_fill(arc.trouble, facts))}",
        f"{hero} listened before acting. {_start(_fill(arc.clue, facts))}",
        f"Inside her helmet, {hero} thought, \"A real hero does not win by being loud. I will notice the danger, protect the small ones, and choose the safest next step.\"",
        f"\"We can help without hurting anyone,\" {hero} said. \"Will you watch the safe path, {companion}?\"",
        f"\"I will,\" said {companion}. \"You watch {grizzly}.\" {_start(_fill(arc.choice, facts))}",
        _start(_fill(arc.action, facts)),
        f"{_start(_fill(arc.rescue, facts))} {grizzly} blinked at {hero}, then gave a slow, friendly nod.",
        f"\"Thank you for seeing the good in me,\" said {grizzly}. \"Thank you for showing us what to do,\" said {companion}.",
        f"The quest ended happily: {_fill(arc.ending, facts)}.",
    ]


ASP_RULES = r"""
setting(brightwood_city).
setting(harbor_hill).
setting(maplebridge_town).
feature(inner_monologue).
feature(quest).
feature(happy_ending).
hero_can_help(S) :- setting(S), feature(inner_monologue), feature(quest), feature(happy_ending).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for setting in SETTING_REGISTRY:
        key = setting.lower().replace(" ", "_")
        lines.append(asp.fact("setting", key))
    for feature in ("inner_monologue", "quest", "happy_ending"):
        lines.append(asp.fact("feature", feature))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A superhero quest about Luna, a grizzly, and a happy rescue."
    )
    parser.add_argument("--setting", choices=list(SETTING_REGISTRY))
    parser.add_argument("--hero")
    parser.add_argument("--companion")
    parser.add_argument("--grizzly")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTING_REGISTRY))
    hero = args.hero or rng.choice(HEROES)
    companion = args.companion or rng.choice(COMPANIONS)
    grizzly = args.grizzly or rng.choice(GRIZZLIES)
    if hero == companion:
        raise StoryError("The hero and companion must have different names.")
    if grizzly in {hero, companion}:
        raise StoryError("The grizzly must have a different name from the human characters.")
    for label, value in (
        ("hero", hero),
        ("companion", companion),
        ("grizzly", grizzly),
    ):
        if not value.strip():
            raise StoryError(f"The {label} name cannot be empty.")
    return StoryParams(setting, hero, companion, grizzly)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTING_REGISTRY:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.hero == params.companion:
        raise StoryError("The hero and companion must have different names.")
    if params.grizzly in {params.hero, params.companion}:
        raise StoryError("The grizzly must have a different name from the human characters.")

    seed = _stable_seed(params)
    arc = ARCS[seed % len(ARCS)]
    world = World(setting=params.setting)

    hero = world.add(
        Entity(
            params.hero,
            "superhero",
            meters={"energy": 1.0, "reach": 1.0},
            memes={"courage": 1.0, "care": 1.0},
        )
    )
    companion = world.add(
        Entity(
            params.companion,
            "helper",
            meters={"mobility": 1.0},
            memes={"alertness": 1.0, "trust": 1.0},
        )
    )
    bear = world.add(
        Entity(
            params.grizzly,
            "grizzly",
            meters={"strength": 1.0, "safety": 0.35},
            memes={"fear": 0.7, "protectiveness": 1.0},
        )
    )
    world.add(
        Entity(
            "the rescue hazard",
            "obstacle",
            meters={"danger": 0.8},
            memes={"confusion": 0.6},
        )
    )
    world.add(
        Entity(
            "the moon shield",
            "gear",
            meters={"light": 1.0, "strength": 0.8},
            memes={"hope": 1.0},
        )
    )

    bear.meters["safety"] = 1.0
    bear.memes["fear"] = 0.1
    world.facts.update(
        arc=arc,
        hero=hero.name,
        companion=companion.name,
        grizzly=bear.name,
        setting=params.setting,
        variant=(seed // len(ARCS)) % 4,
        quest="terminate the danger, scour the path, and rescue the grizzly safely",
        theme="inner monologue, quest, happy ending",
    )

    story = "\n\n".join(_story_lines(world))
    prompts = [
        f"Write a superhero quest in {params.setting} where {params.hero} helps a grizzly named {params.grizzly}.",
        "Tell a child-friendly story using inner monologue, a careful rescue, and a happy ending.",
        "Show that a superhero can terminate danger and scour a path without hurting anyone.",
    ]
    story_qa = [
        QAItem(
            question=f"What trouble did {params.hero} face in \"{arc.title}\"?",
            answer=arc.trouble_answer,
        ),
        QAItem(
            question="What did the hero decide instead of acting recklessly?",
            answer=arc.choice_answer,
        ),
        QAItem(
            question=f"How did {params.hero} help {params.grizzly}?",
            answer=arc.rescue_answer,
        ),
        QAItem(
            question="How did the quest end?",
            answer=f"It ended happily when {_fill(arc.ending, world.facts)}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a grizzly?",
            answer="A grizzly is a large brown bear that needs space, safety, and respect.",
        ),
        QAItem(
            question="What does terminate mean?",
            answer="To terminate something means to bring it safely to an end or stop it.",
        ),
        QAItem(
            question="What does scour mean?",
            answer="To scour means to search or clean an area carefully and thoroughly.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private thought about what to notice or do.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending shows that danger has passed and the characters are safe, wiser, or together.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


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
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            print(
                f"{entity.name}: kind={entity.kind}, "
                f"meters={dict(entity.meters)}, memes={dict(entity.memes)}"
            )
    if qa:
        print("\n== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def _python_valid() -> list[str]:
    return sorted(setting.lower().replace(" ", "_") for setting in SETTING_REGISTRY)


def _asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show hero_can_help/1."))
    return sorted(set(asp.atoms(model, "hero_can_help")))


def asp_verify() -> int:
    expected = {(setting,) for setting in _python_valid()}
    actual = set(_asp_valid())
    if expected != actual:
        print("MISMATCH between clingo and python:")
        print("python only:", sorted(expected - actual))
        print("clingo only:", sorted(actual - expected))
        return 1

    for index, setting in enumerate(SETTING_REGISTRY):
        params = StoryParams(
            setting=setting,
            hero="Luna",
            companion="Pip",
            grizzly="Bruno",
            seed=index,
        )
        sample = generate(params)
        required = ("terminate", "scour", "grizzly")
        if not all(word in sample.story.lower() for word in required):
            print(f"Story vocabulary check failed for {setting}.")
            return 1

    print(f"OK: clingo gate matches python ({len(expected)} settings) and stories pass.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show hero_can_help/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for item in _asp_valid():
            print(item[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, setting in enumerate(SETTING_REGISTRY):
            samples.append(
                generate(
                    StoryParams(
                        setting=setting,
                        hero="Luna",
                        companion="Pip",
                        grizzly="Bruno",
                        seed=base_seed + index,
                    )
                )
            )
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            seed = base_seed + attempt
            attempt += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
            except StoryError as error:
                print(error)
                return
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
