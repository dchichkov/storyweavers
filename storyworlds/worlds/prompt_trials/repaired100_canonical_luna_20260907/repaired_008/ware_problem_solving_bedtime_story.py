#!/usr/bin/env python3
"""
A gentle bedtime storyworld about Luna, a small piece of ware, and solving a
quiet nighttime problem with patience, clues, and a helping friend.
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
    affords: set[str]
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Problem:
    id: str
    missing_ware: str
    clue: str
    hiding_place: str
    solving_action: str
    result: str
    ending_image: str
    answer: str


SETTINGS = {
    "bedroom": Setting(
        "bedroom",
        "the moonlit bedroom",
        {"tea", "music", "storybook"},
    ),
    "nursery": Setting(
        "nursery",
        "the quiet nursery",
        {"tea", "music", "storybook"},
    ),
    "attic_room": Setting(
        "attic_room",
        "the little attic room",
        {"tea", "storybook"},
    ),
}

WARE = {
    "blue_cup": Entity("blue_cup", "ware", "the little blue cup"),
    "star_bowl": Entity("star_bowl", "ware", "the starry bowl"),
    "moon_mug": Entity("moon_mug", "ware", "the moon mug"),
}

PROBLEMS = {
    "tea": Problem(
        "tea",
        "the little blue cup",
        "a round damp mark beside the window",
        "behind the folded quilt",
        "followed the damp mark from the sill to the quilt",
        "the warm milk was safe in the cup, waiting for a sleepy sip",
        "Luna tucked the blue cup beside her pillow, where its painted stars caught the moonlight.",
        "The little blue cup had been moved behind the folded quilt after a breeze nudged the bedside tray.",
    ),
    "music": Problem(
        "music",
        "the starry bowl",
        "one soft jingle beneath the rocking chair",
        "under the rocking chair",
        "listened for the jingle and looked beneath the chair",
        "the music stones were resting safely in the starry bowl",
        "The bowl's tiny stars gleamed while the last music stone made one peaceful chime.",
        "The starry bowl had slipped under the rocking chair when the chair gently rocked.",
    ),
    "storybook": Problem(
        "storybook",
        "the moon mug",
        "a silver thread near the blanket basket",
        "inside the blanket basket",
        "followed the silver thread around the basket",
        "the bedtime story was tucked safely beside the moon mug",
        "The moon mug sat beside the open book as Luna's eyes grew heavy.",
        "The moon mug had been placed inside the blanket basket when the story blanket was folded.",
    ),
}

NAMES = ["Luna", "Mira", "Nia", "Tess", "Iris"]
HELPERS = ["Milo", "Owen", "Pip", "Ari", "Noah"]


@dataclass
class StoryParams:
    place: str
    activity: str
    child: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, sentence: str) -> None:
        self.paragraphs[-1].append(sentence)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


def valid_combos() -> list[tuple[str, str]]:
    return [
        (place_id, activity_id)
        for place_id, setting in SETTINGS.items()
        for activity_id in setting.affords
        if activity_id in PROBLEMS
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A bedtime storyworld about ware and problem solving."
    )
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--activity", choices=sorted(PROBLEMS))
    parser.add_argument("--child")
    parser.add_argument("--helper")
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
    combos = [
        combo
        for combo in valid_combos()
        if args.place is None or combo[0] == args.place
        if args.activity is None or combo[1] == args.activity
    ]
    if not combos:
        raise StoryError("No setting and activity combination supports this bedtime story.")

    place, activity = rng.choice(combos)
    child = args.child or rng.choice(NAMES)
    helper_choices = [name for name in HELPERS if name != child]
    helper = args.helper or rng.choice(helper_choices)
    if child == helper:
        raise StoryError("The child and helper must have different names.")
    return StoryParams(place, activity, child, helper, args.seed)


def tell(setting: Setting, problem: Problem, params: StoryParams) -> World:
    world = World(setting)
    child = world.add(Entity(params.child, "child", params.child))
    helper = world.add(Entity(params.helper, "helper", params.helper))
    ware = world.add(WARE[{
        "tea": "blue_cup",
        "music": "star_bowl",
        "storybook": "moon_mug",
    }[params.activity]])
    world.add(Entity("window", "object", "the window"))
    world.add(Entity("quilt", "object", "the folded quilt"))
    child.memes["sleepiness"] = 0.7
    helper.memes["patience"] = 1.0
    ware.meters["safeness"] = 1.0
    world.facts.update(
        child=child,
        helper=helper,
        ware=ware,
        problem=problem,
        solved=False,
    )

    world.say(
        f"{child.label} was getting ready for bed in {setting.label}, while "
        f"{helper.label} sat nearby with a quiet smile."
    )
    world.say(
        f"Everything was ready for the night, except {ware.label} was not where "
        f"it belonged."
    )

    world.para()
    world.say(
        f"{child.label} looked around slowly. The room felt calm, but the missing "
        f"ware made bedtime seem unfinished."
    )
    world.say(
        f'"I feel worried," said {child.label}. "How can we find it without making a fuss?"'
    )
    world.say(
        f'"We can solve one small clue at a time," said {helper.label}. '
        f'"Let us begin with what we can see."'
    )
    world.say(f"The first clue was {problem.clue}.")

    world.para()
    world.say(
        f"{child.label} did not guess or blame anyone. Instead, {child.label} "
        f"{problem.solving_action}."
    )
    world.say(
        f"The clue led to {problem.hiding_place}, where {ware.label} was waiting."
    )
    world.say(
        f'"There you are," whispered {child.label}. "The room was telling us where to look."'
    )
    world.say(
        f'"And you listened carefully," said {helper.label}. '
        f'"That is how a little problem becomes a little answer."'
    )
    world.facts["solved"] = True
    child.memes["confidence"] = 1.0
    child.memes["sleepiness"] = 1.0
    ware.meters["safeness"] = 2.0

    world.para()
    world.say(f"{problem.result.capitalize()}.")
    world.say(
        f"Together, they put {ware.label} in its proper place and made the room "
        "ready for sleep."
    )
    world.say(problem.ending_image)
    world.say(
        f"{child.label} closed their eyes, knowing that careful looking and kind "
        "questions could help with the next small problem too."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    problem = world.facts["problem"]
    return [
        f"Write a gentle bedtime story about {child.label} and {helper.label} solving a problem with {problem.missing_ware}.",
        f"Tell a quiet problem-solving story set in {world.setting.label}, using a clue and careful searching.",
        f"Write a child-friendly story in which missing ware is found without blame or fear.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    problem = world.facts["problem"]
    ware = world.facts["ware"]
    return [
        QAItem(
            question="Who was getting ready for bed?",
            answer=f"{child.label} was getting ready for bed with help from {helper.label}.",
        ),
        QAItem(
            question="What was missing?",
            answer=f"{ware.label} was missing from its proper place.",
        ),
        QAItem(
            question="What clue helped them solve the problem?",
            answer=f"They noticed {problem.clue}, which led them toward {problem.hiding_place}.",
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They stayed calm, followed the clue, and found {ware.label} {problem.hiding_place}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"They returned the ware to its proper place, and {problem.ending_image}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means noticing what is wrong, looking for useful clues, and trying a careful way to make things right.",
        ),
        QAItem(
            question="What is ware?",
            answer="Ware is a kind of made object, such as a cup or bowl, used for a particular purpose.",
        ),
        QAItem(
            question="Why is it helpful to solve a problem calmly?",
            answer="Being calm helps people notice clues, think clearly, and avoid making the problem bigger.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    lines.append(f"setting: {world.setting.label}")
    for entity in world.entities.values():
        lines.append(
            f"{entity.label}: kind={entity.kind} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"solved={world.facts.get('solved', False)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- setting_registry(S).
activity(A) :- activity_registry(A).
valid(S,A) :- affords(S,A).
ware_for(A,W) :- activity_ware(A,W).
solvable(S,A) :- valid(S,A), ware_for(A,_).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting_registry", setting_id))
        for activity_id in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, activity_id))
    for activity_id in PROBLEMS:
        lines.append(asp.fact("activity_registry", activity_id))
    for activity_id, ware_id in {
        "tea": "blue_cup",
        "music": "star_bowl",
        "storybook": "moon_mug",
    }.items():
        lines.append(asp.fact("activity_ware", activity_id, ware_id))
    return "\n".join(lines)


def asp_program(show: str = "#show solvable/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    python_pairs = set(valid_combos())
    try:
        import asp
        symbols = asp.one_model(asp_program())
        asp_pairs = set(asp.atoms(symbols, "solvable"))
    except ImportError:
        print("OK: Python parity checked; clingo is not installed.")
        return 0
    if asp_pairs != python_pairs:
        print(f"FAIL: ASP pairs {sorted(asp_pairs)} != Python pairs {sorted(python_pairs)}")
        return 1
    for index, params in enumerate(CURATED):
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("solved"):
            print(f"FAIL: curated story {index + 1} did not solve its problem")
            return 1
    print(f"OK: ASP/Python parity and {len(CURATED)} generated stories verified.")
    return 0


CURATED = [
    StoryParams("bedroom", "tea", "Luna", "Milo", 1),
    StoryParams("nursery", "music", "Mira", "Pip", 2),
    StoryParams("attic_room", "storybook", "Nia", "Owen", 3),
]


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.place}")
    if params.activity not in PROBLEMS:
        raise StoryError(f"Unknown activity: {params.activity}")
    if (params.place, params.activity) not in valid_combos():
        raise StoryError(
            f"The activity '{params.activity}' is not available in {SETTINGS[params.place].label}."
        )
    world = tell(SETTINGS[params.place], PROBLEMS[params.activity], params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1")
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < args.n * 50:
            current_seed = base_seed + attempt
            rng = random.Random(current_seed)
            attempt += 1
            trial_args = argparse.Namespace(**vars(args))
            trial_args.seed = current_seed
            params = resolve_params(trial_args, rng)
            sample = generate(params)
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
