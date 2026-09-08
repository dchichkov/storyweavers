#!/usr/bin/env python3
"""
A standalone storyworld about a science-corner problem solved with courage,
careful editing, and shared work.
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
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    helper_name: str
    teacher_name: str
    seed: Optional[int] = None
    scenario_id: int = 0
    rhyme_id: int = 0
    dialogue_id: int = 0
    ending_id: int = 0


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


NAMES = ["Luna", "Milo", "Nell", "Pip", "Tess", "Bram"]
HELPERS = ["Ada", "Jo", "Mina", "Ollie", "Rose", "Theo"]
TEACHERS = ["Ms. June", "Mr. Fox", "Dr. Bea", "Teacher Sam"]

SCENARIOS = [
    {
        "problem": "The tiny hydrant model leaned to one side, and its paper hose sagged weakly.",
        "clue": "Luna noticed that the wide cardboard base had a crack underneath.",
        "method": "They shared craft sticks, folded a new base, and tested the water path one small cup at a time.",
        "result": "The model stood tall and sent a bright blue ribbon of pretend water to the safety sign.",
        "image": "The little hydrant stood proudly on its repaired base, red as a cherry in the corner.",
    },
    {
        "problem": "The science-corner hydrant would not spray its blue ribbon because the straw valve was weak.",
        "clue": "Milo found a soft bend where the straw met the bottle cap.",
        "method": "The children shared tape and a ruler, then strengthened the bend without covering the opening.",
        "result": "A gentle squeeze made the blue ribbon travel through the clear tube.",
        "image": "The repaired hydrant blinked with a bead of blue water beneath its silver cap.",
    },
    {
        "problem": "A sign beside the hydrant had so many words that nobody could understand the safety message.",
        "clue": "Nell read the long sentence aloud and heard that its middle was confusing.",
        "method": "The children shared pencils, crossed out extra words, and edited the message into three clear lines.",
        "result": "Everyone could read STOP, CHECK, and SHARE before touching the model.",
        "image": "The short sign shone beside the hydrant like three tidy stepping stones.",
    },
    {
        "problem": "The hydrant's cardboard wheel was weak and spun backward whenever the class tested it.",
        "clue": "Pip saw that one paper fastener had slipped out of the wheel's center.",
        "method": "The children shared a new fastener and held the wheel steady while Pip made the repair.",
        "result": "The wheel turned forward, and the pretend pressure gauge reached the safe mark.",
        "image": "The wheel rested at the safe mark while the whole group gave a quiet cheer.",
    },
    {
        "problem": "The editor's science report about the hydrant had mixed-up steps.",
        "clue": "Tess discovered that the test result appeared before the question and the plan.",
        "method": "The children shared their notes and reordered the report into ask, build, test, and learn.",
        "result": "The report told the true story of how the weak part was found and fixed.",
        "image": "The finished report lay beside the hydrant, neat as a row of nursery blocks.",
    },
    {
        "problem": "The class had one strong magnifier, so the hydrant's small crack could not be examined by everyone.",
        "clue": "Bram suggested making a turn card so each child would get a careful look.",
        "method": "The children shared the magnifier by taking turns and recorded each observation on one sheet.",
        "result": "Their shared notes showed exactly where the weak seam needed support.",
        "image": "The turn card rested beside the magnifier, with every child's name checked in green.",
    },
]

OPENINGS = [
    "In the science corner, by the window bright, a little hydrant waited in morning light.",
    "Round the science table, where the test tubes gleamed, Luna found a hydrant from a curious dream.",
    "Tap, tap, went the classroom clock, while a red hydrant stood beside a box of chalk.",
    "The science corner hummed a small tune, beneath a paper sun and a silver moon.",
]

DIALOGUES = [
    (
        '"Do not hide the weak part," said the editor. "A true report helps us begin."',
        '"I can check it with you," said the helper. "Then we can share the fix."',
    ),
    (
        '"I am scared I will spoil it," said Luna. "What if the test goes wrong?"',
        '"We will make it safe and small," said the teacher. "Bravery can ask for help."',
    ),
    (
        '"One pair of hands is not enough," said the editor.',
        '"Then let every pair have a turn," said the helper, handing around the tools.',
    ),
    (
        '"The words must match what we saw," said the editor.',
        '"And the work must belong to everyone," said the teacher.',
    ),
]

RHYME_LINES = [
    "They measured with care, in a neat little square, and found that a problem can teach you to share.",
    "They counted, they checked, and they mended the speck; a brave little question can save a weak deck.",
    "With a turn and a try, beneath the blue sky, they learned that shared thinking can help answers fly.",
    "A wobble, a scribble, a careful reply: solve one small problem and give it a try.",
]

ENDINGS = [
    "And so in the science corner, where bright ideas grew, the hydrant stood strong and the report stood true.",
    "The class packed the tools away, but left the sharing card in view for the next curious crew.",
    "From that day on, the children remembered: a brave question, a clear edit, and shared hands make good science.",
    "The little red hydrant rested by the sign, safe and steady in the afternoon shine.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A nursery-rhyme science-corner problem-solving story.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--teacher", choices=TEACHERS)
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
    helper = args.helper or rng.choice([x for x in HELPERS if x != name])
    teacher = args.teacher or rng.choice(TEACHERS)
    return StoryParams(
        name=name,
        helper_name=helper,
        teacher_name=teacher,
        scenario_id=rng.randrange(len(SCENARIOS)),
        rhyme_id=rng.randrange(len(RHYME_LINES)),
        dialogue_id=rng.randrange(len(DIALOGUES)),
        ending_id=rng.randrange(len(ENDINGS)),
    )


def validate_params(params: StoryParams) -> None:
    if not params.name or not params.helper_name or not params.teacher_name:
        raise StoryError("A child, a helper, and a teacher are all needed.")
    if params.name == params.helper_name:
        raise StoryError("The child and helper must have different names.")
    if not 0 <= params.scenario_id < len(SCENARIOS):
        raise StoryError("The chosen science problem is not available.")


def tell(params: StoryParams) -> World:
    validate_params(params)
    scenario = SCENARIOS[params.scenario_id]
    opening = OPENINGS[params.rhyme_id % len(OPENINGS)]
    dialogue = DIALOGUES[params.dialogue_id % len(DIALOGUES)]
    ending = ENDINGS[params.ending_id % len(ENDINGS)]

    world = World()
    child = world.add(Entity("child", "character", "child", params.name))
    helper = world.add(Entity("helper", "character", "child", params.helper_name))
    teacher = world.add(Entity("teacher", "character", "teacher", params.teacher_name))
    hydrant = world.add(Entity("hydrant", "thing", "model", "little hydrant"))
    report = world.add(Entity("report", "thing", "writing", "science report"))
    editor = world.add(Entity("editor", "role", "editor", "editor"))

    child.memes["curiosity"] = 1
    helper.memes["kindness"] = 1
    teacher.memes["patience"] = 1
    hydrant.meters["strength"] = 0.3
    hydrant.memes["importance"] = 1

    world.facts.update(
        child=child,
        helper=helper,
        teacher=teacher,
        hydrant=hydrant,
        report=report,
        editor=editor,
        scenario=scenario,
        resolved=False,
    )

    world.say(opening)
    world.say(
        f"{child.label}, the science-corner editor, worked with {helper.label} and {teacher.label} "
        f"beside a {hydrant.label}. Their plan was to solve a problem, be brave, and share the work."
    )

    world.para()
    world.say(scenario["problem"])
    world.say(f"{child.label} wanted to look away, but {child.label.lower()} took a breath and said, {dialogue[0]}")
    child.memes["worry"] = 1
    hydrant.meters["weakness"] = 1
    world.say(scenario["clue"])

    world.para()
    world.say(dialogue[1])
    helper.memes["support"] = 1
    teacher.memes["guidance"] = 1
    world.say(scenario["method"])
    world.say(RHYME_LINES[params.rhyme_id % len(RHYME_LINES)])
    hydrant.meters["strength"] = 1
    hydrant.meters["weakness"] = 0
    report.meters["clarity"] = 1
    child.memes["worry"] = 0
    child.memes["bravery"] = 1
    helper.memes["sharing"] = 1
    editor.memes["careful_editing"] = 1
    world.say(scenario["result"])

    world.para()
    world.say(f"{child.label} wrote the final observation while {helper.label} checked the tools and {teacher.label} watched the safe test.")
    world.say(ending)
    world.say(scenario["image"])
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    scenario = world.facts["scenario"]
    return [
        "Write a nursery-rhyme story set in a science corner with a hydrant, an editor, and a weak part.",
        f"Show how the children solve this problem: {scenario['problem']}",
        "Include problem solving, bravery, sharing, clear dialogue, and a changed ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    scenario = facts["scenario"]
    child = facts["child"].label
    helper = facts["helper"].label
    return [
        QAItem(
            "Where did the story happen?",
            "It happened in the science corner, beside a small model hydrant.",
        ),
        QAItem(
            "What was weak or wrong with the hydrant project?",
            f"{scenario['problem']} {scenario['clue']}",
        ),
        QAItem(
            f"How did {child} show bravery?",
            f"{child} showed bravery by facing the problem, speaking honestly, and helping test a safe solution instead of hiding the weak part.",
        ),
        QAItem(
            "How did the children share?",
            f"They shared tools, observations, and turns. {helper} helped check the work while everyone contributed to the repair.",
        ),
        QAItem(
            "What changed by the end?",
            f"The children {scenario['method'].lower()} The hydrant became sturdy, and the science report became clear and truthful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does an editor do?", "An editor checks writing and improves it so the ideas are clear and accurate."),
        QAItem("What is a hydrant?", "A hydrant is a connection on a water system that firefighters can use to get water."),
        QAItem("What does weak mean?", "Weak means not strong or not able to hold, push, or work well."),
        QAItem("What is problem solving?", "Problem solving means noticing a difficulty, thinking of possible fixes, and testing a sensible solution."),
        QAItem("Why is sharing useful in science?", "Sharing tools, observations, and ideas lets a group notice more and solve a problem together."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"{entity.id}: {entity.label} meters={meters} memes={memes}")
    lines.append(f"resolved={world.facts.get('resolved')}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(science_corner).
seed_word(hydrant).
seed_word(editor).
seed_word(weak).
feature(problem_solving).
feature(bravery).
feature(sharing).
problem_ok(science_corner, hydrant, weak).
method_ok(problem_solving, bravery, sharing).
valid_story :- problem_ok(science_corner, hydrant, weak),
               method_ok(problem_solving, bravery, sharing).
#show valid_story/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "science_corner"),
            asp.fact("seed_word", "hydrant"),
            asp.fact("seed_word", "editor"),
            asp.fact("seed_word", "weak"),
            asp.fact("feature", "problem_solving"),
            asp.fact("feature", "bravery"),
            asp.fact("feature", "sharing"),
        ]
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    if asp.atoms(model, "valid_story"):
        params = StoryParams("Luna", "Ada", "Ms. June")
        sample = generate(params)
        required = ["hydrant", "editor", "weak", "science corner"]
        if all(word in sample.story.lower() for word in required):
            print("OK: ASP parity matches Python gate and generated story.")
            return 0
    print("MISMATCH")
    return 1


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Luna", "Ada", "Ms. June", scenario_id=0),
    StoryParams("Milo", "Jo", "Mr. Fox", scenario_id=2),
    StoryParams("Nell", "Rose", "Dr. Bea", scenario_id=4),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        print(asp.one_model(asp_program()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
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
