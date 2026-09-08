#!/usr/bin/env python3
"""
A tiny tall-tale storyworld about Luna, a teamwork feature, and the happy ending
that follows when a child acknowledges supervision instead of pretending to work
alone.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

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


@dataclass
class StoryParams:
    place: str
    activity: str
    feature: str
    name: str
    supervisor: str
    trait: str
    scale: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Trial:
    title: str
    opening: str
    obstacle: str
    first_try: str
    clue: str
    teamwork: str
    twist: str
    resolution: str
    ending: str


@dataclass(frozen=True)
class Feature:
    key: str
    label: str
    phrase: str


TRIALS = [
    Trial(
        "the cloud-high cart",
        "Luna built a cart so tall that its handle brushed the lowest cloud.",
        "When she pushed it alone, the cart leaned toward the garden fence.",
        "She puffed out her cheeks and tried to steer it with one elbow.",
        "Her supervisor noticed that the front wheel was turned inward and that the cart was carrying more stones than its frame could safely hold.",
        "Luna acknowledged the supervision, removed half the stones, and asked her teammate to guide the front while she pushed.",
        "The amazing feature was not the cart's height but its little teamwork bell: it rang only when two careful helpers held the handles together.",
        "The cart rolled straight, delivered the stones, and stood proudly beside the new tower.",
        "At sunset, the tower's flag waved above the clouds, while the teamwork bell gave one bright ding for every helper.",
    ),
    Trial(
        "the ladder of ladders",
        "Luna stacked ladders until they looked like a staircase for a giant.",
        "The top rung wobbled whenever she climbed with a bucket of blue paint.",
        "She declared that a tall builder needed no one below and reached for the highest rung.",
        "Her supervisor pointed out that the feet were on soft moss and that no one was watching the base.",
        "Luna acknowledged the supervision, climbed down, and worked with a teammate who steadied the feet while the supervisor checked each joint.",
        "The special feature was a wide safety platform that appeared only after the builders connected their ladders in a team.",
        "The blue paint reached the high sign without a spill.",
        "The finished sign shone above the treetops, and every builder could see their own small handprint in its border.",
    ),
    Trial(
        "the enormous kite",
        "Luna stitched a kite broad enough to shade a picnic from a passing sun.",
        "A sudden gust pulled the kite toward a chimney and tugged its string from her hands.",
        "She chased the string downhill, certain that one fast runner could save the day.",
        "Her supervisor saw that the tail was too short and the wind was turning across the hill.",
        "Luna acknowledged the supervision, called for her teammates, and together they lengthened the tail and held three guide lines.",
        "The hidden feature was a pattern of bright patches that showed which line each teammate should hold.",
        "The kite climbed smoothly and carried a picnic basket to the hilltop.",
        "The kite floated like a second sky, and the basket landed beside the laughing team.",
    ),
    Trial(
        "the whispering bridge",
        "Luna made a bridge from long boards so villagers could cross a puddle swollen to the size of a lake.",
        "The middle board bounced when Luna tested it with one boot.",
        "She planned to run across before the bridge could change its mind.",
        "Her supervisor heard a hollow creak beneath the middle and saw that two supports were not touching firm ground.",
        "Luna acknowledged the supervision, and the team moved the supports, tied a crosspiece, and tested the bridge together.",
        "The bridge's curious feature was a row of wooden chimes that whispered when the supports were balanced.",
        "The chimes stayed quiet, so everyone crossed safely in a slow, steady line.",
        "The little puddle shone under the bridge, and its chimes sang only after the last traveler reached the other side.",
    ),
]


FEATURES = {
    "teamwork": Feature(
        "teamwork",
        "Teamwork",
        "a feature that helps several careful helpers work as one",
    ),
}

NAMES = ["Luna", "Mira", "Nora", "Tessa", "Zoe"]
SUPERVISORS = ["Aunt June", "Coach Rowan", "Grandpa Sol", "Ms. Vale"]
TRAITS = ["bold", "curious", "cheerful", "inventive", "brave"]
SCALES = ["towering", "sky-high", "giant-sized", "cloud-brushing"]


def can_story(place: str, activity: str, feature: str) -> bool:
    return place == "meadow" and activity == "build" and feature == "teamwork"


ASP_RULES = r"""
place(meadow).
activity(build).
feature(teamwork).
supervision(required).
compatible(P,A,F) :- place(P), activity(A), feature(F),
    P = meadow, A = build, F = teamwork.
safe_with_teamwork :- compatible(meadow,build,teamwork), supervision(required).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "meadow"),
            asp.fact("activity", "build"),
            asp.fact("feature", "teamwork"),
            asp.fact("supervision", "required"),
        ]
    )


def asp_program(show: str = "#show compatible/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [("meadow", "build", "teamwork")]


def resolve_params(args: argparse.Namespace, rng: random.Random, seed: int) -> StoryParams:
    if args.place and args.place != "meadow":
        raise StoryError("This tall tale takes place in the meadow.")
    if args.activity and args.activity != "build":
        raise StoryError("This storyworld supports the build activity.")
    if args.feature and args.feature != "teamwork":
        raise StoryError("The required feature is teamwork.")
    if args.supervisor not in {None, *SUPERVISORS}:
        raise StoryError("Choose a listed supervisor.")
    if args.name and args.name not in NAMES:
        raise StoryError("Choose a listed child name.")
    if args.trait and args.trait not in TRAITS:
        raise StoryError("Choose a listed trait.")
    if args.scale and args.scale not in SCALES:
        raise StoryError("Choose a listed tall scale.")

    return StoryParams(
        place="meadow",
        activity="build",
        feature="teamwork",
        name=args.name or rng.choice(NAMES),
        supervisor=args.supervisor or rng.choice(SUPERVISORS),
        trait=args.trait or rng.choice(TRAITS),
        scale=args.scale or rng.choice(SCALES),
        seed=seed,
    )


def tell(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    trial = TRIALS[rng.randrange(len(TRIALS))]
    feature = FEATURES[params.feature]

    world = World()
    luna = world.add(
        Entity(
            "child",
            "character",
            "girl",
            params.name,
            meters={"strength": 1.0, "care": 1.0},
            memes={"confidence": 1.0, "pride": 1.0},
        )
    )
    supervisor = world.add(
        Entity(
            "supervisor",
            "character",
            "adult",
            params.supervisor,
            meters={"attention": 1.0, "experience": 1.0},
            memes={"care": 1.0},
        )
    )
    teammate = world.add(
        Entity(
            "teammate",
            "character",
            "child",
            "Pip",
            meters={"balance": 1.0},
            memes={"friendship": 1.0},
        )
    )
    project = world.add(
        Entity(
            "project",
            "object",
            "building",
            trial.title,
            meters={"stability": 0.0, "height": 2.0},
            memes={"hope": 1.0},
        )
    )

    world.facts.update(
        child=luna,
        supervisor=supervisor,
        teammate=teammate,
        project=project,
        trial=trial,
        feature=feature,
    )

    world.say("In a meadow where the grass tickled the knees of giants, Luna began a very tall project.")
    world.say(
        f"Luna was a {params.trait} builder, and her {params.scale} idea made the birds "
        "fly in a higher-looking V."
    )
    world.say(trial.opening)
    world.say(
        f'"I can finish it alone," {params.name} said. "It is tall, but I am taller in my thinking."'
    )
    world.para()

    world.say(trial.obstacle)
    luna.meters["care"] += 1.0
    luna.memes["pride"] += 1.0
    world.say(trial.first_try)
    world.say(
        f'"Stop and look with me," {params.supervisor} said. '
        f'"Supervision is help, not a heavy hat."'
    )
    world.para()

    world.say(trial.clue)
    world.say(
        f'"I acknowledge your supervision," {params.name} replied. '
        '"I know more when I listen."'
    )
    luna.memes["pride"] -= 1.0
    luna.memes["trust"] = 1.0
    world.fired.add("acknowledge_supervision")

    world.say(trial.teamwork)
    world.say(
        f'"Pip, will you work with me?" {params.name} asked. '
        '"Together," Pip answered, grabbing the other handle.'
    )
    world.fired.add("teamwork")
    project.meters["stability"] = 2.0
    project.memes["hope"] += 1.0
    world.para()

    world.say(trial.twist)
    world.say(trial.resolution)
    world.say(
        f'"The best feature was listening," {params.name} said. '
        '"And the next best feature was having a team."'
    )
    world.para()

    world.say("That evening, the whole meadow applauded.")
    world.say(trial.ending)
    world.facts["title"] = trial.title
    return world


def generation_prompts(world: World) -> list[str]:
    trial = world.facts["trial"]
    child = world.facts["child"]
    return [
        "Write a child-facing Tall Tale about acknowledge, supervision, and a teamwork feature.",
        f"Tell a tall building story in which {child.label} learns to accept supervision.",
        f"Use this turning clue in the story: {trial.clue}",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    supervisor = world.facts["supervisor"]
    teammate = world.facts["teammate"]
    trial = world.facts["trial"]
    return [
        QAItem(
            f"What did {child.label} first want to do?",
            f"{child.label} first wanted to finish the tall project alone.",
        ),
        QAItem(
            "What did the supervision reveal?",
            trial.clue,
        ),
        QAItem(
            f"How did {child.label} acknowledge supervision?",
            f'{child.label} said, "I acknowledge your supervision," and listened to {supervisor.label} before changing the plan.',
        ),
        QAItem(
            "How did teamwork solve the problem?",
            trial.teamwork,
        ),
        QAItem(
            "What showed that the ending was happy?",
            trial.ending,
        ),
        QAItem(
            f"What did {child.label} and {teammate.label} discover about the special feature?",
            "They discovered that the teamwork feature made careful helpers stronger and safer together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does supervision mean?",
            "Supervision means that a responsible, experienced person watches, guides, and helps keep an activity safe.",
        ),
        QAItem(
            "What does acknowledge mean?",
            "Acknowledge means to notice something and openly say that you understand or accept it.",
        ),
        QAItem(
            "What is teamwork?",
            "Teamwork is when people cooperate, share jobs, and help one another reach a goal.",
        ),
        QAItem(
            "What is a feature?",
            "A feature is a useful or noticeable part of a thing.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:10} ({entity.type:10}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A Tall Tale storyworld about supervision and teamwork."
    )
    parser.add_argument("--place", choices=["meadow"])
    parser.add_argument("--activity", choices=["build"])
    parser.add_argument("--feature", choices=["teamwork"])
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--supervisor", choices=SUPERVISORS)
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--scale", choices=SCALES)
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py != clingo:
        print("MISMATCH between Python and ASP:")
        print("  only in Python:", sorted(py - clingo))
        print("  only in ASP:", sorted(clingo - py))
        return 1

    for seed in range(5):
        params = resolve_params(build_parser().parse_args([]), random.Random(seed), seed)
        sample = generate(params)
        required = ("acknowledge", "supervision", "teamwork")
        if not all(word in sample.story.lower() for word in required):
            print(f"Generated story failed keyword check at seed {seed}.")
            return 1
        if not sample.story_qa:
            print(f"Generated story had no story QA at seed {seed}.")
            return 1

    print(f"OK: ASP/Python parity and generated-story checks passed ({len(py)} combos).")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = resolve_params(args, random.Random(base_seed), base_seed)
        samples.append(generate(params))
    else:
        for index in range(max(1, args.n)):
            seed = base_seed + index
            params = resolve_params(args, random.Random(seed), seed)
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
