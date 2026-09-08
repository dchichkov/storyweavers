#!/usr/bin/env python3
"""A heartwarming storyworld about solving a crooked-path problem by thinking straight."""

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
    place: str
    landmark: str
    materials: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Plan:
    id: str
    clue: str
    action: str
    result: str
    image: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

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
    "garden": Setting(
        place="the community garden",
        landmark="the little footbridge",
        materials="smooth stones and willow twine",
    ),
    "courtyard": Setting(
        place="the sunny school courtyard",
        landmark="the rain barrel",
        materials="chalk and flat wooden boards",
    ),
    "orchard": Setting(
        place="the old apple orchard",
        landmark="the red wheelbarrow",
        materials="fallen branches and soft rope",
    ),
}

PLANS = {
    "stream": Plan(
        id="stream",
        clue="Luna noticed that the water was shallowest where three pale stones made a quiet line beneath the ripples.",
        action="They placed sturdy boards across those stones, tied them with willow twine, and tested each board with one careful step.",
        result="The crossing held steady, and the basket reached the seedlings without spilling a drop.",
        image="The new straight walkway shone beside the stream while tiny fish flickered below it.",
    ),
    "wind": Plan(
        id="wind",
        clue="Luna saw that the loose signs always turned toward the same gap between two sheltering trees.",
        action="They moved the signpost into that gap, braced it with flat stones, and tied the corners with a double loop.",
        result="The next gust rattled the leaves but left every sign facing the path.",
        image="The signs pointed straight ahead as bright leaves spun harmlessly around them.",
    ),
    "shadow": Plan(
        id="shadow",
        clue="Luna discovered that the dark patch moved away whenever the morning sun reached the tall sunflower.",
        action="They shifted the seed tray into the sunflower's warm stripe of light and marked its safe place with three pebbles.",
        result="The sprouts opened their small green leaves toward the sun.",
        image="Three pebbles made a neat border around the glowing tray of seedlings.",
    ),
    "rope": Plan(
        id="rope",
        clue="Luna found a short loop in the old rope where a knot had slipped against a rough branch.",
        action="They asked for help, replaced the worn section, and tied a broad knot that everyone could inspect.",
        result="The basket rose smoothly, and nobody had to pull harder than was safe.",
        image="The repaired rope hung straight from the branch, warm in the evening light.",
    ),
}

NAMES = ["Luna", "Milo", "Nia", "Owen", "Tessa", "Pip"]
HELPERS = ["Ari", "Bea", "Cleo", "Finn", "Mara", "Sol"]
OPENINGS = [
    "On a bright morning, a small problem waited quietly.",
    "The day began with a job that looked easy until Luna tried it.",
    "Everyone had a plan, but the garden offered one puzzling surprise.",
    "Before the neighbors arrived, Luna noticed that something was not quite right.",
]
REFLECTIONS = [
    "Luna learned that straight thinking did not mean never making a mistake; it meant looking closely and trying a wise next step.",
    "The friends discovered that a careful question could open the way forward.",
    "Their solution worked because they noticed the clue instead of rushing past it.",
    "When people share ideas kindly, even a small problem can become a path to confidence.",
]


@dataclass
class StoryParams:
    setting: str = "garden"
    plan: str = "stream"
    name: str = "Luna"
    helper_name: str = "Ari"
    opening: int = 0
    reflection: int = 0
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A heartwarming straight problem-solving storyworld.")
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--plan", choices=sorted(PLANS))
    parser.add_argument("--name")
    parser.add_argument("--helper-name")
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
    name = args.name or rng.choice(NAMES)
    choices = [n for n in HELPERS if n != name]
    helper = args.helper_name or rng.choice(choices)
    return StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        plan=args.plan or rng.choice(list(PLANS)),
        name=name,
        helper_name=helper,
        opening=rng.randrange(len(OPENINGS)),
        reflection=rng.randrange(len(REFLECTIONS)),
    )


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.plan not in PLANS:
        raise StoryError(f"Unknown problem-solving plan: {params.plan}")
    if params.name == params.helper_name:
        raise StoryError("The solver and helper must have different names.")

    setting = SETTINGS[params.setting]
    plan = PLANS[params.plan]
    world = World(setting)
    luna = world.add(Entity(params.name, "child", params.name))
    helper = world.add(Entity(params.helper_name, "helper", params.helper_name))
    luna.memes.update({"curiosity": 1.0, "confidence": 0.0, "care": 1.0})
    helper.memes.update({"patience": 1.0, "kindness": 1.0})
    world.facts.update(
        hero=luna,
        helper=helper,
        plan=plan,
        problem_solved=False,
        straight_choice=False,
    )

    world.say(
        f"{OPENINGS[params.opening % len(OPENINGS)]} {luna.label} was helping in {setting.place}, "
        f"near {setting.landmark}. The job was to carry a basket of young plants across the work area, "
        f"but the usual route had become crooked and unsafe."
    )
    world.say(
        f"A loose board pointed one way, a puddle spread another way, and the basket wobbled whenever "
        f"{luna.label} hurried. {luna.label} tried to push ahead, but the basket tipped and one little leaf bent."
    )
    world.para()

    luna.memes["confidence"] = 0.2
    world.say(
        f'"I want to fix this, but I do not know where to begin," said {luna.label}. '
        f'"Let us stop and look for a clue," {helper.label} replied. "We can solve one part at a time."'
    )
    world.say(f"{plan.clue} The friends agreed that going straight did not mean rushing; it meant choosing a clear, safe direction.")
    world.para()

    luna.memes["confidence"] = 1.0
    luna.memes["problem_solving"] = 1.0
    helper.memes["support"] = 1.0
    world.facts["straight_choice"] = True
    world.say(f'"I see the pattern now," said {luna.label}. "We can use what the path is telling us."')
    world.say(f"{plan.action} {helper.label} held the basket while {luna.label} checked each step and thanked the helper for noticing the clue.")
    world.para()

    world.facts["problem_solved"] = True
    luna.memes["confidence"] = 2.0
    luna.memes["joy"] = 1.0
    helper.memes["joy"] = 1.0
    world.say(
        f"{plan.result} {luna.label} smiled, because the answer had not appeared all at once. "
        f"They had observed, asked, tested, and changed the plan when the first idea was not safe."
    )
    world.say(REFLECTIONS[params.reflection % len(REFLECTIONS)])
    world.say(plan.image)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    plan = world.facts["plan"]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            "Write a heartwarming child-friendly story in which a character solves a practical problem by thinking straight.",
            f"Show how {hero.label} and {helper.label} use a clue and careful testing to solve the {plan.id} problem.",
            "End with a concrete image proving that problem solving changed the situation.",
        ],
        story_qa=[
            QAItem(
                f"What problem did {hero.label} need to solve?",
                "The route for carrying the basket had become crooked and unsafe, so the plants needed a steadier way through.",
            ),
            QAItem(
                f"What clue did {hero.label} and {helper.label} notice?",
                plan.clue,
            ),
            QAItem(
                "How did the friends solve the problem?",
                plan.action + " " + plan.result,
            ),
            QAItem(
                "What does going straight mean in this story?",
                "It means looking closely, choosing a clear and safe direction, and taking the next sensible step rather than rushing.",
            ),
            QAItem("What image ends the story?", plan.image),
        ],
        world_qa=[
            QAItem(
                "What is problem solving?",
                "Problem solving is noticing what is wrong, learning from clues, trying a sensible plan, and changing the plan when needed.",
            ),
            QAItem(
                "Why can testing a plan be useful?",
                "Testing a plan in a small and careful way can show whether it is safe and strong before everyone depends on it.",
            ),
            QAItem(
                "What does straight mean?",
                "Straight can describe a line or direction without a bend, and it can also describe being clear, honest, and direct.",
            ),
        ],
        world=world,
    )


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
    lines.append(f"  setting: {world.setting.place}")
    lines.append(f"  landmark: {world.setting.landmark}")
    for entity in world.entities.values():
        lines.append(f"  {entity.label}: memes={entity.memes}")
    lines.append(f"  straight_choice: {world.facts['straight_choice']}")
    lines.append(f"  problem_solved: {world.facts['problem_solved']}")
    return "\n".join(lines)


ASP_RULES = r"""
observed(H) :- hero(H), clue_found(H).
supported(H) :- hero(H), helper(F), helps(F,H).
straight_choice(H) :- observed(H), supported(H), tests_plan(H).
problem_solved(H) :- straight_choice(H), safe_result(H).
#show observed/1.
#show supported/1.
#show straight_choice/1.
#show problem_solved/1.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("hero", "luna"),
            asp.fact("helper", "ari"),
            asp.fact("clue_found", "luna"),
            asp.fact("helps", "ari", "luna"),
            asp.fact("tests_plan", "luna"),
            asp.fact("safe_result", "luna"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    expected = {
        ("observed", ("luna",)),
        ("supported", ("luna",)),
        ("straight_choice", ("luna",)),
        ("problem_solved", ("luna",)),
    }
    model = asp.one_model(asp_program())
    actual = set()
    for symbol in model:
        if symbol.name in {"observed", "supported", "straight_choice", "problem_solved"}:
            actual.add((symbol.name, tuple(str(arg) for arg in symbol.arguments)))
    if actual != expected:
        print("MISMATCH between ASP and Python.")
        print("  asp:", sorted(actual))
        print("  expected:", sorted(expected))
        return 1
    sample = generate(StoryParams())
    if not sample.story or not sample.world.facts["problem_solved"]:
        print("Generated story verification failed.")
        return 1
    print("OK: ASP twin matches the Python story gate and generated story.")
    return 0


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
    if args.verify:
        raise SystemExit(asp_verify())
    if args.show_asp:
        print(asp_program("#show observed/1. #show supported/1. #show straight_choice/1. #show problem_solved/1."))
        return
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("\n".join(sorted(str(atom) for atom in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams(setting=setting, plan=plan, name="Luna", helper_name="Ari", seed=base_seed)
            for setting in SETTINGS
            for plan in PLANS
        ]
    else:
        params_list = []
        for index in range(args.n):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            params_list.append(params)

    samples = [generate(params) for params in params_list]
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
