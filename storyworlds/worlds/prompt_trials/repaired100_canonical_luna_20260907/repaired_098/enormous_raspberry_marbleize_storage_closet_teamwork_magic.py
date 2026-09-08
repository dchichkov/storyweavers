#!/usr/bin/env python3
"""A child-facing slice-of-life story about teamwork and a little magic."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StorageCloset:
    name: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Task:
    object_name: str
    problem: str
    solved: bool = False


@dataclass
class StoryParams:
    seed: Optional[int] = None
    child_name: str = "Luna"
    helper_name: str = "Milo"
    object_name: str = "enormous raspberry marble"
    setting: str = "storage closet"
    route: str = "discovery"


@dataclass(frozen=True)
class TaskPlan:
    worry: str
    first_attempt: str
    obstacle: str
    magic_sign: str
    teamwork_action: str
    solution: str
    lesson: str
    ending: str


@dataclass
class World:
    closet: StorageCloset
    child: Person
    helper: Person
    task: Task
    plan: TaskPlan
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


CLOSET_NAMES = {
    "storage closet": StorageCloset(name="the storage closet"),
    "back storage closet": StorageCloset(name="the back storage closet"),
    "little storage closet": StorageCloset(name="the little storage closet"),
}

CHILDREN = [
    ("Luna", "careful helper"),
    ("Nora", "curious helper"),
    ("Sam", "patient helper"),
    ("Ari", "creative helper"),
]

HELPERS = [
    ("Milo", "box organizer"),
    ("Tess", "shelf checker"),
    ("Jun", "label maker"),
    ("Pia", "basket sorter"),
]

ROUTES = ("discovery", "errand", "rainy_day", "tidying", "after_lunch")

PLANS = {
    "enormous raspberry marble": TaskPlan(
        worry="the enormous raspberry marble was blocking the closet door",
        first_attempt="Luna tried to roll it toward the empty bottom shelf",
        obstacle="the marble bumped into a stack of soft cloths and would not turn",
        magic_sign="a tiny raspberry-colored sparkle appeared wherever two careful hands touched the marble",
        teamwork_action="stood on opposite sides and counted each small push together",
        solution="they made a cloth ramp, moved the boxes aside, and guided the marble into a round padded basket",
        lesson="teamwork makes a large task feel possible when everyone shares a safe part",
        ending="the enormous raspberry marble rested in its basket, glowing softly beside the neatly labeled shelves",
    ),
    "enormous raspberry button": TaskPlan(
        worry="the enormous raspberry button had fallen behind the closet's lowest shelf",
        first_attempt="Luna reached for it with a broom handle",
        obstacle="the button slid farther back whenever the handle touched it",
        magic_sign="the button hummed a warm little note when two people held the shelf steady",
        teamwork_action="held the shelf while Milo swept a wide cloth beneath the button",
        solution="they lifted the shelf together and pulled the button out on the cloth",
        lesson="a good plan listens to the problem before it pushes harder",
        ending="the enormous raspberry button shone on a labeled craft shelf instead of hiding in the dust",
    ),
    "enormous raspberry spool": TaskPlan(
        worry="the enormous raspberry spool had tangled the string cart in the storage closet",
        first_attempt="Luna tugged one loose-looking strand",
        obstacle="the tug pulled three other strands into a tighter knot",
        magic_sign="a soft spark traveled along the string whenever the children paused and listened",
        teamwork_action="held the spool still while Milo followed one strand at a time",
        solution="they unwound the safe outer loop, cut one damaged piece, and stored the string in a box",
        lesson="patience and shared attention can untangle what force only tightens",
        ending="the enormous raspberry spool sat calmly in its box, with one bright strand ready for tomorrow",
    ),
    "enormous raspberry cushion": TaskPlan(
        worry="the enormous raspberry cushion had tipped across the closet walkway",
        first_attempt="Luna tried to drag it under the coat hooks",
        obstacle="the cushion caught on a basket and made the shelf wobble",
        magic_sign="a faint glow appeared under the cushion whenever someone said, 'Together'",
        teamwork_action="lifted one corner at a time while counting slowly",
        solution="they moved the basket first, folded the cushion, and placed it on the wide top shelf",
        lesson="teamwork means making room for one another as well as moving things",
        ending="the enormous raspberry cushion rested safely overhead, leaving a clear path through the closet",
    ),
}

OBJECTS = tuple(PLANS)


ASP_RULES = r"""
person(luna).
person(helper).
closet(storage_closet).
object(enormous_raspberry_marble).
teamwork(person(luna),person(helper)).
magic(object(enormous_raspberry_marble)).
safe_plan :- teamwork(person(luna),person(helper)), magic(object(enormous_raspberry_marble)).
solved(enormous_raspberry_marble) :- safe_plan.
valid_story :- solved(enormous_raspberry_marble).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("person", "luna"),
        asp.fact("person", "helper"),
        asp.fact("closet", "storage_closet"),
        asp.fact("object", "enormous_raspberry_marble"),
        asp.fact("teamwork", "luna", "helper"),
        asp.fact("magic", "enormous_raspberry_marble"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/1."))
    actual = set(asp.atoms(model, "solved"))
    expected = {("enormous_raspberry_marble",)}
    if actual == expected:
        print("OK: clingo gate matches python reasoning.")
        return 0
    print("MISMATCH between clingo and python reasoning.")
    print("clingo:", sorted(actual))
    print("python:", sorted(expected))
    return 1


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(
        str(value)
        for value in (
            params.seed,
            params.child_name,
            params.helper_name,
            params.object_name,
            params.setting,
            params.route,
        )
    )
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def build_world(params: StoryParams) -> World:
    if params.setting not in CLOSET_NAMES:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.object_name not in PLANS:
        raise StoryError(f"Unknown object: {params.object_name}")
    if not params.child_name.strip() or not params.helper_name.strip():
        raise StoryError("Character names cannot be empty.")
    closet_template = CLOSET_NAMES[params.setting]
    child_role = next((role for name, role in CHILDREN if name == params.child_name), "careful helper")
    helper_role = next((role for name, role in HELPERS if name == params.helper_name), "helpful organizer")
    return World(
        closet=StorageCloset(name=closet_template.name),
        child=Person(name=params.child_name, role=child_role),
        helper=Person(name=params.helper_name, role=helper_role),
        task=Task(
            object_name=params.object_name,
            problem=PLANS[params.object_name].worry,
        ),
        plan=PLANS[params.object_name],
    )


def tell_story(world: World, params: StoryParams) -> None:
    child = world.child
    helper = world.helper
    closet = world.closet
    plan = world.plan
    rng = story_rng(params)

    child.memes.update(curiosity=1.0, courage=0.0)
    helper.memes.update(patience=1.0, helpfulness=1.0)

    openings = {
        "discovery": (
            f"After lunch, {child.name} opened {closet.name} and found that {plan.worry}. "
            f"The object was so bright that it looked like a berry-colored moon."
        ),
        "errand": (
            f"{child.name} went to {closet.name} to fetch a roll of tape. "
            f"Instead, {child.name} discovered that {plan.worry}."
        ),
        "rainy_day": (
            f"Rain drummed on the windows while {child.name} and {helper.name} tidied {closet.name}. "
            f"Behind a basket, they saw that {plan.worry}."
        ),
        "tidying": (
            f"{child.name} had promised to make one shelf neat before snack. "
            f"In {closet.name}, that promise became harder when {plan.worry}."
        ),
        "after_lunch": (
            f"The room smelled of crayons and clean paper when {child.name} checked {closet.name}. "
            f"Right beside the door, {plan.worry}."
        ),
    }
    world.say(openings[params.route])
    world.say(
        rng.choice(
            [
                f"It was enormous, raspberry-colored, and much too awkward for one person to manage alone.",
                f"The strange object seemed ordinary at first, but its enormous raspberry shape filled the narrow space.",
                f"A little magic clung to it, though nobody knew what the magic would do yet.",
            ]
        )
    )
    world.say(
        f'"I can help," {helper.name} said. "{child.name}, let us make a plan before we move it."'
    )

    world.para()
    world.say(f"First, {plan.first_attempt}.")
    world.say(f"But {plan.obstacle}.")
    world.say(
        rng.choice(
            [
                f'"Pushing harder is not helping," {child.name} said. "{helper.name}, what do you notice?"',
                f'"Wait," said {helper.name}. "The closet is telling us to try a different way."',
                f"{child.name} stopped and looked closely. Then {child.name} noticed that {plan.magic_sign}.",
            ]
        )
    )
    world.say(f"That was the magic: {plan.magic_sign}.")
    world.say(f'"We can share the work," {helper.name} said. "{child.name} agreed and {plan.teamwork_action}.')

    world.para()
    world.say(
        rng.choice(
            [
                f"Their first push was tiny. Their second push was steadier. Soon, {plan.solution}.",
                f"They did not rush. With each count, they made space for one another, and {plan.solution}.",
                f"Magic helped only after they listened to each other. Working carefully, {plan.solution}.",
            ]
        )
    )
    child.memes["courage"] = 1.0
    child.meters["safe_steps"] = 4.0
    helper.meters["shared_tasks"] = 1.0
    world.task.solved = True
    world.closet.meters["clear_path"] = 1.0
    world.closet.memes["calm"] = 1.0

    world.para()
    world.say(
        rng.choice(
            [
                f"{child.name} smiled because {plan.lesson}.",
                f'"That felt like magic," {child.name} said. {helper.name} nodded. "It was teamwork magic."',
                f"They left a small note on the shelf: {plan.lesson.capitalize()}.",
            ]
        )
    )
    world.say(f"By snack time, {plan.ending}.")
    world.facts.update(
        child=child,
        helper=helper,
        closet=closet,
        task=world.task,
        plan=plan,
        solved=True,
        teamwork=True,
        magic=True,
    )


def generation_prompts(world: World) -> list[str]:
    plan = world.plan
    return [
        f"Write a slice-of-life story about {world.child.name} and {world.helper.name} in {world.closet.name}.",
        f"Show teamwork and gentle magic as the characters solve this problem: {plan.worry}.",
        f"End with this changed image: {plan.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.child.name
    helper = world.helper.name
    plan = world.plan
    return [
        QAItem(
            question=f"What problem did {child} and {helper} find in the storage closet?",
            answer=f"They found that {plan.worry}. The object was too awkward for one person to handle safely.",
        ),
        QAItem(
            question="What first attempt did not work?",
            answer=f"{child} tried to help by {plan.first_attempt}, but {plan.obstacle}.",
        ),
        QAItem(
            question="How did magic appear in the story?",
            answer=f"The magic appeared when {plan.magic_sign}. It responded after the children slowed down and worked together.",
        ),
        QAItem(
            question="How did the characters use teamwork?",
            answer=f"They {plan.teamwork_action}. Sharing the task helped them solve the problem without rushing.",
        ),
        QAItem(
            question="How did the storage closet change by the end?",
            answer=f"They {plan.solution}. As a result, {plan.ending}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a storage closet?",
            answer="A storage closet is a small place where supplies and objects are kept until they are needed.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people share a task, listen to one another, and work toward the same safe goal.",
        ),
        QAItem(
            question="What is magic in this story world?",
            answer="Magic is a gentle wonder that appears when people pay attention, cooperate, and make a thoughtful choice.",
        ),
        QAItem(
            question="Why should people make a plan before moving a large object?",
            answer="A plan helps people notice obstacles, divide the work, and avoid unsafe pushing or pulling.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A slice-of-life storage closet story about teamwork and magic."
    )
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--setting", choices=sorted(CLOSET_NAMES))
    parser.add_argument("--child-name")
    parser.add_argument("--helper-name")
    parser.add_argument("--object", dest="object_name", choices=sorted(PLANS))
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(sorted(CLOSET_NAMES))
    child_name, _ = rng.choice(CHILDREN)
    helper_name, _ = rng.choice(HELPERS)
    object_name = args.object_name or rng.choice(sorted(PLANS))
    return StoryParams(
        seed=args.seed,
        child_name=args.child_name or child_name,
        helper_name=args.helper_name or helper_name,
        object_name=object_name,
        setting=setting,
        route=rng.choice(ROUTES),
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for person in (world.child, world.helper):
        lines.append(
            f"{person.name}: role={person.role!r} meters={person.meters} memes={person.memes}"
        )
    lines.append(
        f"{world.closet.name}: meters={world.closet.meters} memes={world.closet.memes}"
    )
    lines.append(
        f"task: object={world.task.object_name!r} problem={world.task.problem!r} "
        f"solved={world.task.solved}"
    )
    lines.append("features: teamwork=True magic=True")
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
        print("\n== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solved/1."))
        print(sorted(set(asp.atoms(model, "solved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = 3 if args.all else args.n
    if count < 1:
        raise StoryError("The number of stories must be at least 1.")

    samples: list[StorySample] = []
    for index in range(count):
        params = resolve_params(args, random.Random(base_seed + index))
        params.seed = base_seed + index
        samples.append(generate(params))

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
