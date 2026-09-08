#!/usr/bin/env python3
"""
A child-facing mystery about probation, suspense, and earning back trust.

Luna must complete a careful probation task after a mistake. When the town's
silver compass disappears, she follows clues instead of blaming anyone, and
learns that trust grows through honest, observable choices.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    id: str
    label: str
    affordances: set[str]
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Case:
    id: str
    disappearance: str
    suspicion: str
    clue: str
    hidden_cause: str
    luna_action: str
    solution: str
    proof: str
    ending: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "lantern_hall": Setting(
        id="lantern_hall",
        label="the Lantern Hall",
        affordances={"probation_trial"},
        meters={"shelter": 1.0, "visibility": 0.8},
        memes={"trust": 0.7, "tension": 0.5},
    )
}

CASES = {
    "silver_compass": Case(
        id="silver_compass",
        disappearance="the silver compass vanished from its locked display",
        suspicion="some people whispered that Luna had taken it to prove she could still be trusted",
        clue="a thin trail of blue wax led from the display toward the map cupboard",
        hidden_cause="a loose display hinge had let the compass slide into the map cupboard when the evening door slammed",
        luna_action="knelt near the cupboard and followed the wax marks without touching the lock",
        solution="opened the cupboard with the keeper's key and found the compass behind a rolled map",
        proof="the hinge was repaired, the compass was returned, and the wax trail matched the door seal",
        ending="the silver compass shone in its repaired case while Luna's name joined the hall's list of careful helpers",
    ),
    "bell_key": Case(
        id="bell_key",
        disappearance="the brass key to the evening bell was missing before the storm watch",
        suspicion="several watchers guessed that Luna had hidden it after being placed on probation",
        clue="a line of damp sand crossed the threshold beneath the rain cloak",
        hidden_cause="the key had caught in the cloak's inside pocket when the bell keeper hurried indoors",
        luna_action="held a lantern low and followed the sand line beneath the row of cloaks",
        solution="asked the bell keeper to check every pocket before anyone searched another person's things",
        proof="the key was found in the damp pocket, and the keeper's muddy footprints matched the path",
        ending="the bell rang safely above the roofs, and Luna recorded the checking steps for the next watch",
    ),
    "blue_ribbon": Case(
        id="blue_ribbon",
        disappearance="the blue ribbon marking the safest bridge path disappeared from the notice board",
        suspicion="the crowd feared that Luna had removed it to make her probation task look easier",
        clue="two fresh pinholes appeared beside a row of dripping leaves",
        hidden_cause="the ribbon had been carried outside on a wet coat and pinned to the wrong board",
        luna_action="compared the pinholes with the boards along the covered walkway",
        solution="moved the ribbon back, added a weatherproof sign, and checked the path with two witnesses",
        proof="the bridge route was clear, and both witnesses could explain where the ribbon belonged",
        ending="the blue ribbon fluttered under its new cover as Luna crossed the bridge with the others",
    ),
}

NAMES = ["Luna", "Mira", "Nell", "Tavi", "Orin"]
TRAITS = ["patient", "curious", "careful", "brave", "honest"]

OPENINGS = [
    "At dusk, the Lantern Hall filled with gold light and quiet questions.",
    "The Lantern Hall kept maps, bells, and promises behind its old green door.",
    "On the first evening of Luna's probation, rain tapped the roof like tiny fingers.",
    "Everyone in the valley knew that the Lantern Hall trusted actions more than speeches.",
]

REFLECTIONS = [
    "Trust is rebuilt one careful choice at a time.",
    "Probation is not a label that lasts forever; it is a chance to show changed behavior.",
    "A mystery should be tested with clues before it is answered with blame.",
    "Being watched can feel tense, but honest steps make the truth easier to see.",
]


@dataclass
class StoryParams:
    place: str
    case: str
    hero_name: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [
        (place, case_id)
        for place, setting in SETTINGS.items()
        for case_id in CASES
        if "probation_trial" in setting.affordances
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A suspenseful mystery storyworld about probation and trust."
    )
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--case", choices=sorted(CASES))
    parser.add_argument("--name", dest="hero_name")
    parser.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.place:
        combos = [combo for combo in combos if combo[0] == args.place]
    if args.case:
        combos = [combo for combo in combos if combo[1] == args.case]
    if not combos:
        raise StoryError(
            "No compatible probation story exists for the selected place and case."
        )
    place, case_id = rng.choice(combos)
    return StoryParams(
        place=place,
        case=case_id,
        hero_name=args.hero_name or rng.choice(NAMES),
        trait=args.trait or rng.choice(TRAITS),
        seed=args.seed,
    )


def build_world(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.case not in CASES:
        raise StoryError(f"Unknown mystery case: {params.case}")

    setting = SETTINGS[params.place]
    case = CASES[params.case]
    world = World(setting=setting)

    hero = world.add(
        Entity(
            id="hero",
            kind="child",
            label=params.hero_name,
            meters={"care": 0.4, "risk": 0.2},
            memes={"trust": 0.35, "courage": 0.6, "tension": 0.7},
        )
    )
    keeper = world.add(
        Entity(
            id="keeper",
            kind="adult",
            label="the hall keeper",
            meters={"attention": 0.8},
            memes={"trust": 0.45, "patience": 0.8},
        )
    )
    friend = world.add(
        Entity(
            id="friend",
            kind="child",
            label="Pip",
            meters={"curiosity": 0.8},
            memes={"trust": 0.6, "tension": 0.6},
        )
    )
    compass = world.add(
        Entity(
            id="missing_object",
            kind="object",
            label="the missing object",
            meters={"importance": 0.9},
            memes={"mystery": 0.9},
        )
    )

    world.facts.update(
        hero=hero,
        keeper=keeper,
        friend=friend,
        compass=compass,
        case=case,
        reflection="",
        probation_task="complete the evening watch by checking the hall's map, door, and display",
        evidence_step="",
        resolved=False,
    )

    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    rng = random.Random(params.seed)
    case: Case = world.facts["case"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    keeper: Entity = world.facts["keeper"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]

    opening = rng.choice(OPENINGS)
    reflection = rng.choice(REFLECTIONS)
    safe_action = rng.choice(
        [
            "write down each fact before making a guess",
            "ask permission before opening any cupboard",
            "keep the original arrangement untouched until a witness arrived",
            "check the clue twice from different angles",
        ]
    )
    world.facts["reflection"] = reflection
    world.facts["evidence_step"] = safe_action

    hero.memes["tension"] = 0.8
    keeper.memes["trust"] = 0.5

    world.say(opening)
    world.say(
        f"{hero.label} was on probation after rushing through a supply check the week before. "
        f"Tonight, the {params.trait} child had one chance to show a better way: "
        f"{world.facts['probation_task']}."
    )
    world.say(
        f"The hall keeper watched from the doorway while {friend.label} helped carry a lantern. "
        f"Then {case.disappearance}."
    )

    world.para()
    world.say(
        f"A cold hush moved through the hall. {case.suspicion.capitalize()}."
    )
    world.say(
        f'"I did not take it," {hero.label} said. "But I can help find out what happened."'
    )
    world.say(
        f'"Then begin with what we know," said {keeper.label}. "No blaming, and no secret searching."'
    )
    world.say(
        f"{hero.label} took a breath and decided to {safe_action}. "
        f"The first clue was {case.clue}."
    )

    hero.meters["care"] = 0.9
    hero.memes["tension"] = 0.6
    friend.memes["trust"] = 0.75

    world.para()
    world.say(f"{hero.label} {case.luna_action}.")
    world.say(
        f'"The mark starts near the display," {friend.label} whispered. '
        f'"It does not point to Luna. It points somewhere else."'
    )
    world.say(
        f'"Good noticing," {hero.label} replied. "Let us ask before we touch anything."'
    )
    world.say(
        f"The keeper unlocked the cupboard. The truth was simple but hidden: {case.hidden_cause}."
    )
    world.say(
        f"{hero.label} {case.solution}. The evidence mattered because {case.proof}."
    )

    hero.memes["trust"] = 0.85
    hero.memes["tension"] = 0.2
    keeper.memes["trust"] = 0.9
    world.facts["resolved"] = True

    world.para()
    world.say(
        f"The keeper marked the probation task complete. "
        f'"You made a mistake before," said {keeper.label}, "but tonight you showed your change through your choices."'
    )
    world.say(
        f"{hero.label} smiled. " + reflection
    )
    world.say(f"By morning, {case.ending}.")

    return world


def generation_prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    return [
        f"Write a suspenseful child-facing mystery about {hero.label} completing probation when {case.disappearance}.",
        f"Tell a mystery in which {hero.label} follows {case.clue} instead of blaming someone.",
        "Write a story showing that probation can become a fair chance to rebuild trust through careful actions.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Why was {hero.label} on probation?",
            answer=(
                f"{hero.label} was on probation because the child had rushed through a supply check. "
                "The probation task gave the child a chance to show more careful behavior."
            ),
        ),
        QAItem(
            question="What disappeared from the hall?",
            answer=f"{case.disappearance.capitalize()}.",
        ),
        QAItem(
            question="Why did the mystery feel suspenseful?",
            answer=(
                f"People were unsure what had happened, and {case.suspicion}. "
                f"The suspense eased when the clue appeared: {case.clue}."
            ),
        ),
        QAItem(
            question="How did Luna investigate safely?",
            answer=(
                f"Luna chose to {world.facts['evidence_step']}. "
                "The child asked permission, preserved the scene, and followed evidence instead of making a rushed accusation."
            ),
        ),
        QAItem(
            question="What caused the disappearance?",
            answer=f"The real cause was that {case.hidden_cause}.",
        ),
        QAItem(
            question="How did Luna rebuild trust?",
            answer=(
                f"Luna rebuilt trust by staying honest, making a careful investigation, and helping prove that {case.proof}. "
                "The keeper could trust the child's actions because other people could observe them."
            ),
        ),
    ]


KNOWLEDGE = [
    QAItem(
        question="What is probation?",
        answer=(
            "Probation is a period when someone has extra rules and supervision after a mistake, "
            "while they show through their actions that they can be trusted again."
        ),
    ),
    QAItem(
        question="What is suspense?",
        answer=(
            "Suspense is the feeling of wondering what will happen next, especially when an important answer is not known yet."
        ),
    ),
    QAItem(
        question="What is a mystery?",
        answer=(
            "A mystery is a question or puzzling event that people solve by collecting and comparing clues."
        ),
    ),
    QAItem(
        question="Why should people check clues before blaming someone?",
        answer=(
            "People should check clues first because a quick guess can be unfair, while evidence may reveal a different explanation."
        ),
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/2.
valid(P, C) :- place(P), case(C), affords(P, probation_trial).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for affordance in sorted(setting.affordances):
            lines.append(asp.fact("affords", place, affordance))
    for case_id in CASES:
        lines.append(asp.fact("case", case_id))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_combos = set(valid_combos())
    asp_combos = set(asp_valid_combos())
    if python_combos != asp_combos:
        print("Mismatch between Python and ASP compatibility gates.")
        print("Only in Python:", sorted(python_combos - asp_combos))
        print("Only in ASP:", sorted(asp_combos - python_combos))
        return 1

    for seed in range(3):
        rng = random.Random(seed)
        params = resolve_params(
            argparse.Namespace(place=None, case=None, hero_name=None, trait=None),
            rng,
        )
        params.seed = seed
        sample = generate(params)
        if not sample.story or not sample.story_qa:
            print("Generated story verification failed.")
            return 1

    print(f"OK: ASP/Python parity holds for {len(python_combos)} combinations.")
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"setting: {world.setting.label}")
    for entity in world.entities.values():
        lines.append(
            f"{entity.label}: meters={entity.meters}; memes={entity.memes}"
        )
    lines.append(f"resolved: {world.facts.get('resolved')}")
    lines.append(f"probation task: {world.facts.get('probation_task')}")
    return "\n".join(lines)


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
        place="lantern_hall",
        case="silver_compass",
        hero_name="Luna",
        trait="careful",
        seed=96096,
    ),
    StoryParams(
        place="lantern_hall",
        case="bell_key",
        hero_name="Mira",
        trait="honest",
        seed=96097,
    ),
    StoryParams(
        place="lantern_hall",
        case="blue_ribbon",
        hero_name="Tavi",
        trait="curious",
        seed=96098,
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible probation stories:\n")
        for place, case_id in combos:
            print(f"  {place:16} {case_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        target = max(1, args.n)
        while len(samples) < target and attempts < target * 50:
            seed = base_seed + attempts
            attempts += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
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
