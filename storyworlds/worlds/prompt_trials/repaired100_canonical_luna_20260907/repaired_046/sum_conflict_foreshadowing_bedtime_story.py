#!/usr/bin/env python3
"""A gentle bedtime story about a missing sum, a small conflict, and a clue seen early."""

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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)

from results import QAItem, StoryError, StorySample  # noqa: E402


SETTINGS = {
    "attic": "the quiet attic room",
    "garden": "the moonlit garden",
    "library": "the little library",
}

CHILDREN = ["Luna", "Mira", "Nora", "Pip", "Tess"]
HELPERS = ["Oren", "Milo", "Sage", "Bea", "Finn"]
TREASURES = ["silver buttons", "blue pebbles", "paper stars", "warm acorns"]

ASP_RULES = r"""
#show valid_setting/1.
#show valid_treasure/1.
valid_setting(attic).
valid_setting(garden).
valid_setting(library).
valid_treasure(silver_buttons).
valid_treasure(blue_pebbles).
valid_treasure(paper_stars).
valid_treasure(warm_acorns).
"""


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    setting: str = SETTINGS["attic"]
    hero: str = "Luna"
    companion: str = "Oren"
    treasure: str = "silver buttons"
    seed: Optional[int] = None


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass(frozen=True)
class Incident:
    name: str
    object_name: str
    problem: str
    early_clue: str
    conflict: str
    hero_action: str
    companion_action: str
    resolution: str
    ending_image: str
    sum_total: int


INCIDENTS = [
    Incident(
        "the button moon",
        "a bedtime counting tray",
        "the silver buttons were scattered before the final count",
        "a faint silver button trail curved toward the old rocking chair",
        "Luna thought Oren had moved the buttons, while Oren thought Luna had counted too quickly",
        "count the buttons in small groups beside the candle",
        "look beneath the rocking chair and follow the shining trail",
        "they found every button and made the sum twelve",
        "twelve silver buttons gleamed in a neat moon-shaped row",
        12,
    ),
    Incident(
        "the pebble bridge",
        "a little pebble bridge",
        "one blue pebble was missing from the bridge beside the window",
        "a blue dust mark crossed the sill toward a sleeping fern",
        "Luna wanted to rebuild at once, but Oren said the missing pebble might still be nearby",
        "write the known groups of pebbles and add them carefully",
        "search around the fern without bending its quiet leaves",
        "they found the pebble and checked that the sum was fifteen",
        "fifteen blue pebbles made a tiny bridge beneath the stars",
        15,
    ),
    Incident(
        "the paper sky",
        "a paper-star garland",
        "the garland had fewer stars than its nighttime pattern required",
        "one golden thread trembled beside the basket of folded paper",
        "Luna blamed the draft, while Oren worried that a star had fallen",
        "add the stars on each side of the garland",
        "search softly under the rug and behind the storybooks",
        "they found the loose star and proved the sum was ten",
        "ten paper stars rested above them like a patient little sky",
        10,
    ),
    Incident(
        "the acorn nest",
        "a woodland counting nest",
        "the warm acorns no longer matched the number on the nest card",
        "tiny crumbs led from the card to a sleeping toy squirrel",
        "Luna wanted to erase the card, but Oren asked them to inspect the nest first",
        "sort the acorns into groups and add the groups",
        "lift the toy squirrel gently and return the hidden acorn",
        "they found the full sum of eighteen",
        "eighteen warm acorns made the nest ready for morning",
        18,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A bedtime storyworld about a careful sum.")
    parser.add_argument("--setting", choices=list(SETTINGS))
    parser.add_argument("--hero", choices=CHILDREN)
    parser.add_argument("--companion", choices=HELPERS)
    parser.add_argument("--treasure", choices=TREASURES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting_key = args.setting or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(CHILDREN)
    companion_choices = [name for name in HELPERS if name != hero]
    companion = args.companion or rng.choice(companion_choices)
    if companion == hero:
        raise StoryError("The hero and companion must have different names.")
    treasure = args.treasure or rng.choice(TREASURES)
    return StoryParams(
        setting=SETTINGS[setting_key],
        hero=hero,
        companion=companion,
        treasure=treasure,
    )


def _incident(params: StoryParams) -> Incident:
    seed = params.seed if params.seed is not None else 0
    return INCIDENTS[seed % len(INCIDENTS)]


def tell(params: StoryParams) -> World:
    if params.hero == params.companion:
        raise StoryError("A bedtime conflict needs two different speakers.")

    incident = _incident(params)
    world = World(params=params)

    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            label=params.hero,
            role="hero",
            meters={"sleepiness": 0.2, "worry": 0.2, "curiosity": 0.8},
            memes={"patience": 0.5, "trust": 0.8},
            traits=["careful"],
        )
    )
    companion = world.add(
        Entity(
            id="companion",
            kind="character",
            label=params.companion,
            role="companion",
            meters={"sleepiness": 0.3, "worry": 0.1},
            memes={"patience": 0.8, "trust": 0.8},
            traits=["observant"],
        )
    )
    treasure = world.add(
        Entity(
            id="treasure",
            kind="thing",
            label=params.treasure,
            role="counting material",
            meters={"counted": 0.0},
            memes={"wonder": 0.7},
            traits=["small", "shiny"],
        )
    )

    world.say(f"At bedtime, {hero.label} and {companion.label} sat in {params.setting}.")
    world.say(
        f"They were arranging {treasure.label} for a quiet counting game before the last lamp was turned low."
    )
    world.say(
        f"Earlier, {hero.label} had noticed that {incident.early_clue}; the clue seemed small, so they tucked it into memory."
    )
    world.say(
        f"“Let us find the sum before sleep,” said {hero.label}. “Then the counting tray will be ready for tomorrow.”"
    )

    world.para()
    world.say(f"But {incident.problem}.")
    world.say(f"The number on their card did not match the things before them, and {incident.conflict}.")
    hero.meters["worry"] += 0.4
    companion.meters["worry"] += 0.3
    hero.memes["trust"] -= 0.1
    companion.memes["trust"] -= 0.1
    world.say(
        f"“You must have moved them,” said {hero.label}. “I counted them carefully.”"
    )
    world.say(
        f"“Maybe the card is wrong,” answered {companion.label}. “Let us not quarrel while the moon is listening.”"
    )

    world.para()
    world.say(
        f"Then the early clue returned to {hero.label}'s thoughts: {incident.early_clue}."
    )
    world.say(
        f"“You are right,” said {hero.label}. “We should look for what changed before we choose someone to blame.”"
    )
    world.say(
        f"{hero.label} decided to {incident.hero_action}, while {companion.label} promised to {incident.companion_action}."
    )
    hero.memes["patience"] += 0.5
    companion.memes["patience"] += 0.2
    hero.memes["trust"] += 0.3
    companion.memes["trust"] += 0.3
    world.say(
        f"Together they followed the clue, and {incident.resolution}."
    )
    treasure.meters["counted"] = float(incident.sum_total)

    world.para()
    world.say(
        f"The small conflict grew quiet. Neither child had been careless or unkind; they had simply needed a better look."
    )
    world.say(
        f"“A sum is more than a number,” whispered {companion.label}. “It can show us how the pieces belong together.”"
    )
    world.say(
        f"{hero.label} smiled. “And a clue can help us find the missing piece.”"
    )
    hero.meters["worry"] = 0.0
    companion.meters["worry"] = 0.0
    world.say(
        f"They placed the card beside the completed {incident.object_name}, and {incident.ending_image}."
    )
    world.say("Then the lamp went dark, and the room kept their careful answer safe until morning.")

    world.facts.update(
        hero=hero,
        companion=companion,
        treasure=treasure,
        setting=params.setting,
        incident=incident,
        problem=incident.problem,
        early_clue=incident.early_clue,
        conflict=incident.conflict,
        hero_action=incident.hero_action,
        companion_action=incident.companion_action,
        resolution=incident.resolution,
        ending_image=incident.ending_image,
        sum_total=incident.sum_total,
        dialogue=True,
        conflict_resolved=True,
        foreshadowing_paid=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    hero = facts["hero"]
    companion = facts["companion"]
    return [
        f"Write a gentle bedtime story about {hero.label} and {companion.label} finding the correct sum.",
        f"Include a small conflict, dialogue, and the foreshadowed clue that {facts['early_clue']}.",
        "End with a peaceful image proving that the missing piece was found.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"]
    companion = facts["companion"]
    incident = facts["incident"]
    return [
        QAItem(
            question=f"What problem did {hero.label} and {companion.label} face?",
            answer=f"They faced a counting problem because {incident.problem}, so the number on their card did not match what they could see.",
        ),
        QAItem(
            question="What clue foreshadowed the solution?",
            answer=f"The clue was that {incident.early_clue}. They remembered it later and used it to search carefully.",
        ),
        QAItem(
            question=f"Why did {hero.label} and {companion.label} disagree?",
            answer=f"They disagreed because {incident.conflict}. Their worry made each child suspect a different explanation.",
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They solved it by having one child {incident.hero_action} and the other {incident.companion_action}. Together, they discovered that {incident.resolution}.",
        ),
        QAItem(
            question="What was the final sum?",
            answer=f"The final sum was {incident.sum_total}. They checked the pieces together before putting the card beside the finished arrangement.",
        ),
        QAItem(
            question="How did the conflict change?",
            answer="The conflict became peaceful when the children stopped blaming each other, followed the clue, and checked the evidence together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sum?",
            answer="A sum is the answer found by adding numbers or groups together.",
        ),
        QAItem(
            question="Why can clues be useful?",
            answer="Clues can point toward what happened and help people make a careful choice instead of guessing.",
        ),
        QAItem(
            question="What can friends do during a disagreement?",
            answer="Friends can speak kindly, listen to each other, look at the evidence, and solve the problem together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.extend(["", "== story qa =="])
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.extend(["", "== world qa =="])
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: kind={entity.kind} meters={entity.meters} memes={entity.memes} traits={entity.traits}"
        )
    incident = world.facts.get("incident")
    if incident:
        lines.append(
            f"facts: sum_total={world.facts['sum_total']} "
            f"conflict_resolved={world.facts['conflict_resolved']} "
            f"foreshadowing_paid={world.facts['foreshadowing_paid']} "
            f"incident={incident.name}"
        )
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    lines = []
    for key in SETTINGS:
        lines.append(asp.fact("setting", key))
    for treasure in TREASURES:
        safe = treasure.replace(" ", "_")
        lines.append(asp.fact("treasure", safe))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_setting/1.\n#show valid_treasure/1."))
    settings = sorted(asp.atoms(model, "valid_setting"))
    treasures = sorted(asp.atoms(model, "valid_treasure"))
    expected_settings = sorted((key,) for key in SETTINGS)
    expected_treasures = sorted((treasure.replace(" ", "_"),) for treasure in TREASURES)
    if settings != expected_settings or treasures != expected_treasures:
        print("MISMATCH: ASP registries do not match Python registries.")
        return 1

    for index, params in enumerate(
        [
            StoryParams(setting=SETTINGS["attic"], hero="Luna", companion="Oren", treasure="silver buttons", seed=index)
            for index in range(len(INCIDENTS))
        ]
    ):
        sample = generate(params)
        if str(sample.facts if hasattr(sample, "facts") else sample.story) == "":
            print("MISMATCH: generated story was empty.")
            return 1
        if params.hero not in sample.story or params.companion not in sample.story:
            print("MISMATCH: generated story lost its characters.")
            return 1
    print("OK: ASP registries and generated story checks match.")
    return 0


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


CURATED = [
    StoryParams(SETTINGS["attic"], "Luna", "Oren", "silver buttons", 0),
    StoryParams(SETTINGS["garden"], "Mira", "Sage", "blue pebbles", 1),
    StoryParams(SETTINGS["library"], "Nora", "Bea", "paper stars", 2),
    StoryParams(SETTINGS["attic"], "Pip", "Finn", "warm acorns", 3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_setting/1.\n#show valid_treasure/1."))
        return

    if args.verify:
        try:
            sys.exit(asp_verify())
        except ImportError:
            print("ASP verification requires clingo.")
            sys.exit(1)

    if args.asp:
        print("Valid settings:")
        for key, value in SETTINGS.items():
            print(f"  {key}: {value}")
        print("Valid counting materials:")
        for treasure in TREASURES:
            print(f"  {treasure}")
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            rng = random.Random(base_seed + attempts)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempts
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempts += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.hero} and {sample.params.companion} at {sample.params.setting}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
