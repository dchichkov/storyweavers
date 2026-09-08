#!/usr/bin/env python3
"""A child-friendly pirate reconciliation tale about a number, a gruff voice, and rotten treasure."""

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
    "cove": "Moonbeam Cove",
    "island": "Parrot Island",
    "harbor": "Starfish Harbor",
}
CAPTAINS = ["Luna", "Mara", "Pip", "Tess", "Nico"]
CREWMATES = ["Bo", "Finn", "Sable", "Poppy", "Juno"]
TREASURES = ["silver buttons", "cinnamon biscuits", "blue glass beads"]


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
    setting: str = "Moonbeam Cove"
    captain: str = "Luna"
    crewmate: str = "Bo"
    treasure: str = "silver buttons"
    seed: Optional[int] = None


@dataclass(frozen=True)
class Trouble:
    name: str
    number: int
    object_name: str
    problem: str
    clue: str
    gruff_line: str
    captain_job: str
    crewmate_job: str
    repair: str
    result: str
    ending_image: str


TROUBLES = [
    Trouble(
        "the rotten chest",
        7,
        "a treasure chest",
        "the chest's wooden lid had gone rotten around its brass hinge",
        "seven pale wood chips lay beside the hinge",
        "“Seven chips mean seven guesses, and every guess is foolish!”",
        "count the sound hinges",
        "find a dry board and a coil of rope",
        "replace the rotten strip and bind the hinge with rope",
        "the lid opened safely, and all seven silver buttons stayed inside",
        "seven silver buttons glittered beneath a lid no longer green with rot",
    ),
    Trouble(
        "the spoiled map",
        3,
        "a treasure map",
        "three corners of the map had become rotten after a damp night",
        "three dry reeds rested beside the map table",
        "“Three corners, three troubles! No map can save this crew!”",
        "number the safe landmarks",
        "press dry cloth beneath the weak corners",
        "copy the route onto fresh sailcloth",
        "the crew could follow the new map without tearing the old one",
        "three red stars shone on a strong sailcloth map",
    ),
    Trouble(
        "the rotten barrel",
        5,
        "a water barrel",
        "five little leaks dripped from a rotten band around the barrel",
        "five dark rings marked the places where water escaped",
        "“Five leaks! I say we roll the barrel into the sea!”",
        "count and mark the leaks",
        "fetch corks and a strip of canvas",
        "plug each leak and wrap the band with canvas",
        "the barrel held enough water for the whole voyage",
        "five corks bobbed like tiny hats while the barrel stayed full",
    ),
    Trouble(
        "the crooked sign",
        4,
        "a dock sign",
        "four rotten nails made the welcome sign sag toward the tide",
        "four rusty nail heads rested below the crooked post",
        "“Four nails down means four reasons to give up!”",
        "hold the sign straight",
        "bring fresh nails and a smooth plank",
        "replace the rotten post edge and fasten the sign",
        "the welcome words faced every arriving sailor",
        "four bright nails held the sign above a calm, welcoming dock",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a pirate reconciliation tale.")
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--captain", choices=CAPTAINS)
    parser.add_argument("--crewmate", choices=CREWMATES)
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
    captain = args.captain or rng.choice(CAPTAINS)
    crewmate = args.crewmate or rng.choice(CREWMATES)
    if captain == crewmate:
        choices = [name for name in CREWMATES if name != captain]
        crewmate = rng.choice(choices)
    treasure = args.treasure or rng.choice(TREASURES)
    return StoryParams(
        setting=SETTINGS[setting_key],
        captain=captain,
        crewmate=crewmate,
        treasure=treasure,
    )


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


def _trouble_for(params: StoryParams) -> Trouble:
    seed = params.seed if params.seed is not None else 0
    return TROUBLES[seed % len(TROUBLES)]


def tell(params: StoryParams) -> World:
    if params.captain == params.crewmate:
        raise StoryError("The captain and crewmate must be different people.")

    world = World(params=params)
    captain = world.add(
        Entity(
            id="captain",
            kind="character",
            label=params.captain,
            role="captain",
            meters={"courage": 2.0, "patience": 1.0},
            memes={"trust": 1.0, "calm": 1.0},
            traits=["careful"],
        )
    )
    crewmate = world.add(
        Entity(
            id="crewmate",
            kind="character",
            label=params.crewmate,
            role="crewmate",
            meters={"courage": 1.0, "patience": 1.0},
            memes={"trust": 1.0, "calm": 0.0},
            traits=["strong-voice"],
        )
    )
    treasure = world.add(
        Entity(
            id="treasure",
            kind="thing",
            label=params.treasure,
            role="treasure",
            meters={"value": 1.0},
            memes={"hope": 1.0},
        )
    )

    trouble = _trouble_for(params)
    world.facts.update(
        trouble=trouble,
        captain=captain,
        crewmate=crewmate,
        treasure=treasure,
        disagreement=True,
        repaired=False,
        reconciled=False,
    )

    world.say(f"At {params.setting}, Captain {captain.label} sailed beneath a purple morning sky.")
    world.say(
        f"Captain {captain.label} and {crewmate.label} were guarding {treasure.label} "
        f"when they discovered {trouble.problem}."
    )
    world.say(
        f"“The number {trouble.number} is important,” said {captain.label}. "
        f"“We must count the damage before we choose a fix.”"
    )
    world.say(f"{crewmate.label} gave a gruff huff. “{trouble.gruff_line}”")

    world.para()
    world.say(
        f"Their words bumped like ships in a narrow harbor. "
        f"Then {captain.label} noticed that {trouble.clue}."
    )
    world.say(
        f"“I sounded gruff,” {crewmate.label} admitted. "
        f"“I was worried the rotten part would ruin our treasure.”"
    )
    world.say(
        f"{captain.label} lowered the spyglass. “I was worried too. "
        f"Let us forgive the sharp words and work together.”"
    )
    world.say(
        f"They shared a small smile, and their disagreement softened into a plan."
    )

    world.para()
    world.say(
        f"Captain {captain.label} decided to {trouble.captain_job}, "
        f"while {crewmate.label} agreed to {trouble.crewmate_job}."
    )
    world.say(f"Together they {trouble.repair}.")
    world.say(f"After {trouble.number} careful checks, {trouble.result}.")
    captain.memes["trust"] += 2.0
    crewmate.memes["trust"] += 2.0
    captain.memes["calm"] += 1.0
    crewmate.memes["calm"] += 2.0
    world.facts["repaired"] = True
    world.facts["reconciled"] = True

    world.para()
    world.say(
        f"“I am sorry for calling your plan foolish,” said {crewmate.label}. "
        f"“And I am sorry I did not listen sooner,” said {captain.label}."
    )
    world.say(
        f"They shook hands beside the mast and shared the {treasure.label} "
        f"with every sailor on deck."
    )
    world.say(f"The final sight was bright and clear: {trouble.ending_image}.")
    return world


def generation_prompts(world: World) -> list[str]:
    trouble: Trouble = world.facts["trouble"]
    captain: Entity = world.facts["captain"]
    crewmate: Entity = world.facts["crewmate"]
    return [
        f"Write a child-friendly pirate tale in which {captain.label} and {crewmate.label} repair {trouble.object_name}.",
        f"Use the number {trouble.number}, the word gruff, and the word rotten in a story about reconciliation.",
        f"Include pirate dialogue that helps {captain.label} and {crewmate.label} forgive one another.",
    ]


def story_qa(world: World) -> list[QAItem]:
    trouble: Trouble = world.facts["trouble"]
    captain: Entity = world.facts["captain"]
    crewmate: Entity = world.facts["crewmate"]
    treasure: Entity = world.facts["treasure"]
    return [
        QAItem(
            question=f"What went wrong with {trouble.object_name}?",
            answer=f"{trouble.problem.capitalize()}.",
        ),
        QAItem(
            question=f"How did the number {trouble.number} help the pirates?",
            answer=f"They used the number {trouble.number} to count or check the damaged parts before choosing a safe repair.",
        ),
        QAItem(
            question=f"Why did {crewmate.label} sound gruff at first?",
            answer=f"{crewmate.label} sounded gruff because the rotten damage made the crewmate worry that {treasure.label} might be ruined.",
        ),
        QAItem(
            question=f"How did {captain.label} and {crewmate.label} reconcile?",
            answer=f"They admitted that their sharp words came from worry, apologized to each other, divided the work, and repaired the trouble together.",
        ),
        QAItem(
            question="What proved that their reconciliation worked?",
            answer=f"After they worked together, {trouble.result}. They could share the treasure peacefully again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace after a disagreement by listening, apologizing, and finding a way to work together.",
        ),
        QAItem(
            question="What does rotten mean?",
            answer="Rotten means spoiled, decayed, or weakened, often because something has been damaged or left damp for too long.",
        ),
        QAItem(
            question="Why is counting useful when repairing something?",
            answer="Counting helps people notice how much is damaged, plan carefully, and check that every part has been fixed.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.label}: meters={entity.meters} memes={entity.memes} traits={entity.traits}"
        )
    trouble: Trouble = world.facts["trouble"]
    lines.append(
        f"trouble={trouble.name}; number={trouble.number}; "
        f"repaired={world.facts['repaired']}; reconciled={world.facts['reconciled']}"
    )
    return "\n".join(lines)


ASP_RULES = r"""
#show valid_setting/1.
#show valid_number/1.
#show valid_reconciliation/1.

valid_setting(cove).
valid_setting(island).
valid_setting(harbor).

valid_number(3).
valid_number(4).
valid_number(5).
valid_number(7).

valid_reconciliation(apology).
valid_reconciliation(listening).
valid_reconciliation(shared_repair).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for key in SETTINGS:
        lines.append(asp.fact("setting", key))
    for trouble in TROUBLES:
        lines.append(asp.fact("number", trouble.number))
    for item in ("apology", "listening", "shared_repair"):
        lines.append(asp.fact("reconciliation", item))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    settings = sorted(set(asp.atoms(model, "valid_setting")))
    numbers = sorted(set(asp.atoms(model, "valid_number")))
    reconciliations = sorted(set(asp.atoms(model, "valid_reconciliation")))

    expected_settings = sorted((key,) for key in SETTINGS)
    expected_numbers = sorted({(trouble.number,) for trouble in TROUBLES})
    expected_reconciliations = sorted(
        (item,) for item in ("apology", "listening", "shared_repair")
    )

    if (
        settings != expected_settings
        or numbers != expected_numbers
        or reconciliations != expected_reconciliations
    ):
        print("MISMATCH")
        return 1

    for seed in range(len(TROUBLES)):
        params = StoryParams(
            setting=SETTINGS["cove"],
            captain="Luna",
            crewmate="Bo",
            treasure=TREASURES[0],
            seed=seed,
        )
        sample = generate(params)
        if "reconciled" not in sample.story or "rotten" not in sample.story:
            print("MISMATCH: generated story lost required state.")
            return 1

    print("OK: ASP registry parity and generated-story checks passed.")
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
    StoryParams(
        setting=SETTINGS["cove"],
        captain="Luna",
        crewmate="Bo",
        treasure=TREASURES[0],
        seed=0,
    ),
    StoryParams(
        setting=SETTINGS["island"],
        captain="Mara",
        crewmate="Finn",
        treasure=TREASURES[1],
        seed=1,
    ),
    StoryParams(
        setting=SETTINGS["harbor"],
        captain="Tess",
        crewmate="Poppy",
        treasure=TREASURES[2],
        seed=2,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print("Valid settings:")
        for key, value in SETTINGS.items():
            print(f"  {key}: {value}")
        print("Valid repair numbers:", ", ".join(str(t.number) for t in TROUBLES))
        print("Reconciliation steps: apology, listening, shared repair")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        target = max(1, args.n)
        while len(samples) < target and index < max(target * 50, 50):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            params = sample.params
            header = f"### {params.captain} and {params.crewmate} at {params.setting}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
