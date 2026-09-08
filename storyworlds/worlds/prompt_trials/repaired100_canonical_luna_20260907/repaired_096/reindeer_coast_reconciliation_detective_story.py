#!/usr/bin/env python3
"""
A child-facing detective storyworld about reindeer, a coast, and reconciliation.
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
    conflict: str
    clue: str
    false_lead: str
    revelation: str
    action: str
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
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "windward_cove": Setting(
        "windward_cove",
        "the windward coast",
        {"footprints", "tide_pools", "driftwood", "signal_lantern"},
        {"distance": 0.0, "wind": 0.8, "visibility": 0.7},
        {"belonging": 0.6, "trust": 0.4},
    )
}

REINDEER = {
    "luna": Entity(
        "luna",
        "reindeer",
        "Luna the reindeer",
        {"height": 1.4, "speed": 0.7},
        {"curiosity": 0.9, "patience": 0.8},
    ),
    "orin": Entity(
        "orin",
        "reindeer",
        "Orin the reindeer",
        {"height": 1.3, "speed": 0.8},
        {"pride": 0.7, "worry": 0.6},
    ),
    "mara": Entity(
        "mara",
        "reindeer",
        "Mara the reindeer",
        {"height": 1.2, "speed": 0.6},
        {"kindness": 0.8, "worry": 0.5},
    ),
}

CASES = {
    "shell_lantern": Case(
        "shell_lantern",
        "the silver shell lantern disappeared before the evening coast walk",
        "Orin accused Mara because she had borrowed it last, while Mara felt certain that someone had moved it without asking",
        "three damp hoofprints stopped beside a driftwood arch, and a thread of red wool clung to the lantern hook",
        "a row of gull feathers that seemed to point toward Orin's shelter",
        "the hoofprints belonged to Luna, and the red wool came from a rescue blanket; the lantern had been carried to the tide pool so its light could guide a stranded seal pup",
        "asked each reindeer what they had seen, followed the prints only as far as the tide line, and invited Orin and Mara to inspect the wool together",
        "the lantern was found beside the seal pup, and both reindeer agreed that blame had hidden the useful facts",
        "the reindeer hung the lantern between their shelters, where its silver light shone across the forgiving coast",
    ),
    "blue_rope": Case(
        "blue_rope",
        "the blue safety rope vanished from the cliff path",
        "Mara blamed Orin for taking it to mark a racing track, while Orin stopped listening because he felt judged",
        "salt crystals formed a blue-white line from the path to a stack of storm boards",
        "a hoof-shaped dent beside the racing track",
        "the rope had been moved by both reindeer: Orin used it to pull a loose board, and Mara later carried it toward the cliff without knowing he had already helped",
        "reconstructed the order of events and let each reindeer correct the parts that did not fit",
        "the rope was returned to the path, and the two reindeer learned that a true clue can still tell only half a story",
        "they tied the rope with two bright knots, one chosen by each reindeer, before walking the safe path together",
    ),
    "map_leaf": Case(
        "map_leaf",
        "the leaf map showing the safest route home was torn at the coast",
        "Orin thought Mara had hidden the missing piece to win an argument, and Mara answered sharply because she had been trying to repair it",
        "tiny green scraps rested beneath a sleeping seal's warm rock",
        "a fresh scratch on Mara's storage box",
        "the seal pup had dragged the map piece under the rock, while Mara had saved the remaining piece from the rain",
        "compared every scrap, listened without interrupting, and asked what each reindeer had done before the map was noticed missing",
        "the map was restored and both reindeer saw that their separate actions had protected it",
        "the repaired map hung on a driftwood board as Luna led the reindeer home beneath a clearing sky",
    ),
}

NAMES = ["Luna", "Orin", "Mara", "Nori", "Tavi"]
TRAITS = ["careful", "curious", "patient", "bright-eyed", "thoughtful"]

@dataclass
class StoryParams:
    place: str
    case: str
    hero_name: str
    trait: str
    seed: Optional[int] = None


OPENINGS = [
    "At dusk, the windward coast glittered like a trail of clues.",
    "The tide whispered against the windward coast when the trouble began.",
    "Everyone on the windward coast knew that small tracks could tell large stories.",
]

REFLECTIONS = [
    "Reconciliation begins when people listen for the whole truth instead of collecting reasons to blame.",
    "A careful detective repairs trust by checking facts and making room for every voice.",
    "Saying sorry matters, but understanding what happened helps a friendship grow strong again.",
]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, case_id) for place, setting in SETTINGS.items() for case_id in CASES if "footprints" in setting.affordances]


def explain_rejection() -> str:
    return "The chosen coast must support footprints so the detective can follow physical clues."


def build_world(params: StoryParams) -> World:
    if (params.place, params.case) not in valid_combos():
        raise StoryError(explain_rejection())
    setting = SETTINGS[params.place]
    case = CASES[params.case]
    world = World(setting)
    hero = world.add(Entity(params.hero_name.lower(), "reindeer", params.hero_name))
    orin = world.add(REINDEER["orin"])
    mara = world.add(REINDEER["mara"])
    helper = world.add(REINDEER["luna"])
    rng = random.Random(params.seed)
    opening = rng.choice(OPENINGS)
    reflection = rng.choice(REFLECTIONS)
    question = rng.choice([
        "What happened before anyone began blaming another reindeer?",
        "Which detail did you notice first?",
        "Can we follow the clue without deciding who is guilty?",
    ])
    answer = rng.choice([
        "We can check the facts together before we choose a side.",
        "Yes. A clue should lead us to what happened, not merely to whom we fear.",
        "Let us listen to both stories and see whether the pieces fit.",
    ])

    world.facts.update(
        hero=hero,
        orin=orin,
        mara=mara,
        helper=helper,
        case=case,
        reflection=reflection,
        question=question,
        answer=answer,
        resolved=True,
    )

    world.say(opening)
    world.say(
        f"{hero.label}, a {params.trait} young reindeer, helped keep watch over the shore with "
        f"{orin.label} and {mara.label}."
    )
    world.say(f"Then {case.disappearance}.")
    world.para()
    world.say(f"{case.conflict}.")
    world.say(f'"{question}" asked {hero.label}.')
    world.say(f'"{answer}" replied {helper.label}.')
    world.say(f"{hero.label} began the investigation by recording the first solid clue: {case.clue}.")
    world.say(f"A tempting false lead appeared: {case.false_lead}.")
    world.para()
    world.say(
        f"Instead of chasing the false lead, {hero.label} {case.action}. "
        f"The tide, the wool, and the hoofprints showed that {case.revelation}."
    )
    world.say(
        f"Orin lowered his antlers. Mara lowered hers too. They discovered that {case.proof}."
    )
    world.say(
        f"They spoke honestly, apologized for the hurtful guesses, and agreed to check with one another before "
        f"turning a worry into an accusation."
    )
    world.para()
    world.say(f"The lesson was clear: {reflection}")
    world.say(case.ending)
    return world


KNOWLEDGE = [
    QAItem(
        "What is reconciliation?",
        "Reconciliation is the process of repairing a relationship after people have been hurt or disagreed.",
    ),
    QAItem(
        "What is a detective clue?",
        "A detective clue is a detail that helps explain what happened.",
    ),
    QAItem(
        "What is a coast?",
        "A coast is the land beside a sea or ocean.",
    ),
    QAItem(
        "What is a reindeer?",
        "A reindeer is a deer with antlers; both males and females can grow them.",
    ),
]


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    hero = world.facts["hero"]
    return [
        f"Write a child-facing detective story on a coast where {case.disappearance}.",
        f"Tell a reindeer mystery in which {hero.label} follows this clue: {case.clue}.",
        "Write a gentle reconciliation story showing how listening and evidence repair a friendship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]
    hero: Entity = world.facts["hero"]
    return [
        QAItem(
            "What mystery did the reindeer investigate?",
            f"They investigated why {case.disappearance}.",
        ),
        QAItem(
            "What clue moved the investigation forward?",
            f"The important clue was {case.clue}.",
        ),
        QAItem(
            "Why did the detective avoid the false lead?",
            f"The detective avoided it because {case.false_lead} could distract everyone from the physical evidence.",
        ),
        QAItem(
            "What did the reindeer discover?",
            f"They discovered that {case.revelation}.",
        ),
        QAItem(
            "How did reconciliation happen?",
            f"{hero.label} helped the reindeer listen to one another, apologize for their accusations, and agree to check facts together.",
        ),
    ]


ASP_RULES = r"""
#show valid/2.
valid(P, C) :- place(P), case(C), affords(P, footprints), has_clue(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for affordance in setting.affordances:
            lines.append(asp.fact("affords", place, affordance))
    for case_id, case in CASES.items():
        lines.append(asp.fact("case", case_id))
        if case.clue:
            lines.append(asp.fact("has_clue", case_id))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(asp.one_model(asp_program()), "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo_result = set(asp_valid_combos())
    if py != clingo_result:
        print("ASP/Python mismatch.")
        print("Only Python:", sorted(py - clingo_result))
        print("Only ASP:", sorted(clingo_result - py))
        return 1
    rng = random.Random(17)
    for _ in range(3):
        params = resolve_params(build_parser().parse_args([]), rng)
        sample = generate(params)
        if not sample.story or "reindeer" not in sample.story.lower():
            print("Generated-story verification failed.")
            return 1
    print(f"OK: ASP/Python parity holds for {len(py)} combinations; generated stories pass.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=list(KNOWLEDGE),
        world=world,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    case = args.case or rng.choice(list(CASES))
    if (place, case) not in valid_combos():
        raise StoryError(explain_rejection())
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, case, name, trait, args.seed)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"setting: {world.setting.label}")
    for entity in world.entities.values():
        lines.append(
            f"{entity.label}: kind={entity.kind}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"case: {world.facts['case'].id}")
    lines.append("resolved: True")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Reindeer coast reconciliation detective storyworld.")
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--case", choices=CASES)
    parser.add_argument("--name")
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


CURATED = [
    StoryParams("windward_cove", "shell_lantern", "Luna", "curious", 960),
    StoryParams("windward_cove", "blue_rope", "Nori", "patient", 961),
    StoryParams("windward_cove", "map_leaf", "Tavi", "thoughtful", 962),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        for place, case in asp_valid_combos():
            print(f"{place}: {case}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(args.n):
            seed = base_seed + index
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            samples.append(generate(params))

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
