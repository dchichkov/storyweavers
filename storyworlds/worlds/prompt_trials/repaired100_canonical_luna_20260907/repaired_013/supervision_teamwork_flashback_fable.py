#!/usr/bin/env python3
"""
A small fable world about supervision, teamwork, and remembering a past lesson.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    setting: str = "the hillside mill"
    leader: str = "Mara"
    helper: str = "Pip"
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
    "the hillside mill": {"mood": "bright, busy, and windy"},
    "the cedar bridge": {"mood": "green, creaky, and high above the stream"},
    "the little orchard": {"mood": "golden, leafy, and full of bees"},
}

LESSONS = [
    {
        "title": "The Bell and the Broken Cart",
        "problem": "A cart of grain stuck beside a steep mill path, and rushing made its loose wheel wobble worse.",
        "choice": "Mara watched the work closely, then asked Pip to inspect the wheel instead of pulling harder.",
        "action": "Pip remembered a lesson from an earlier storm: one worker should steady the cart while another tied a rope below the axle.",
        "result": "Their careful teamwork lifted the wheel over the stone, and the grain reached the mill before sunset.",
        "memory": "Last spring, a patient supervisor had shown Pip how a small warning could prevent a large fall.",
        "problem_answer": "A grain cart was stuck on the steep path, and its loose wheel could become more dangerous if they rushed.",
        "choice_answer": "Mara supervised calmly and asked Pip to inspect the wheel before anyone pulled the cart.",
        "result_answer": "Pip recalled an earlier lesson, and the two workers used different jobs together to move the cart safely.",
        "ending": "the mill bell rang while the repaired wheel rested under the warm eaves",
    },
    {
        "title": "The Orchard Gate",
        "problem": "A fallen branch blocked the orchard gate just as ripe apples needed to be carried inside.",
        "choice": "Mara did not order everyone to push at once; she watched the hinges and gave each helper a clear task.",
        "action": "Pip flashed back to a rainy morning when an old keeper had taught him to lift first and pull second.",
        "result": "The branch rose without scraping the young trees, and every basket passed through the gate.",
        "memory": "The old keeper's voice returned to Pip: a team is strongest when each paw knows where the others are.",
        "problem_answer": "A heavy branch blocked the orchard gate while ripe apples waited outside.",
        "choice_answer": "Mara supervised the helpers and assigned careful jobs instead of letting everyone push randomly.",
        "result_answer": "Pip remembered how to lift before pulling, so the team opened the gate without harming the trees.",
        "ending": "one red apple remained on the branch above the newly opened gate",
    },
    {
        "title": "The Bridge of Three Ropes",
        "problem": "One rope on the cedar bridge snapped while a family of mice waited with a basket of acorns.",
        "choice": "Mara asked Pip to check the knots, and she stood where she could see both the bridge and the frightened travelers.",
        "action": "Pip remembered crossing a smaller bridge under supervision, when he had learned to test every knot before trusting his weight.",
        "result": "The team replaced the rope, guided the mice across one by one, and left the bridge firmer than before.",
        "memory": "In that old memory, a wise watcher had said, \"Good supervision sees the danger before the danger sees you.\"",
        "problem_answer": "A rope snapped on the bridge while mice waited to carry their acorns across.",
        "choice_answer": "Mara supervised from a safe place while Pip inspected the knots before the team crossed.",
        "result_answer": "Pip remembered to test every knot, and the team replaced the rope and helped the mice cross safely.",
        "ending": "three new knots shone beside the stream like small brown bracelets",
    },
]


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum((index + 1) * ord(char) for index, char in enumerate(
        "|".join((params.setting, params.leader, params.helper))
    ))


def _fill(text: str, facts: dict[str, object]) -> str:
    return text.format(**facts)


def generate(params: StoryParams) -> StorySample:
    if params.leader == params.helper:
        raise StoryError("The supervisor and helper must be different characters.")
    if params.setting not in SETTING_REGISTRY:
        raise StoryError(f"Unknown setting: {params.setting}")

    number = _stable_seed(params)
    lesson = LESSONS[number % len(LESSONS)]
    world = World(params.setting)
    leader = world.add(Entity(params.leader, "supervisor", memes={"care": 1.0, "supervision": 1.0}))
    helper = world.add(Entity(params.helper, "helper", memes={"curiosity": 1.0, "teamwork": 1.0}))
    rope = world.add(Entity("the strong rope", "tool", meters={"length": 1.0, "strength": 1.0}))
    cart = world.add(Entity("the waiting cart", "object", meters={"stability": 0.2}))
    world.facts.update(
        leader=leader.name,
        helper=helper.name,
        setting=params.setting,
        lesson=lesson,
        title=lesson["title"],
        memory=lesson["memory"],
        opening_variant=(number // len(LESSONS)) % 3,
    )
    f = world.facts
    title = lesson["title"]
    openings = [
        f"At {params.setting}, where the {SETTING_REGISTRY[params.setting]['mood']} air carried every sound, {params.leader} supervised the day's work.",
        f"One bright morning in {params.setting}, {params.leader} and {params.helper} began a task that looked easy until it did not.",
        f"The animals of {params.setting} knew a simple rule: a careful eye and a willing paw can make a strong team.",
    ]
    story = "\n\n".join([
        openings[f["opening_variant"]],
        f"{lesson['problem']} \"Should we pull now?\" asked {params.helper}. \"First we look,\" said {params.leader}.",
        lesson["choice"],
        f"Then {params.helper} remembered something. {lesson['memory']} The old scene returned like a picture in a pond: {lesson['action']}",
        f"\"I know what to do,\" said {params.helper}. \"And I will watch your side,\" answered {params.leader}. Together, {lesson['action'][0].lower() + lesson['action'][1:]}",
        lesson["result"],
        f"When the work was done, {lesson['ending']}. The fable taught that supervision is not bossing, teamwork is not rushing, and a remembered lesson can help many paws move as one.",
    ])
    prompts = [
        f"Write a fable about supervision and teamwork at {params.setting}.",
        "Include a flashback in which a character remembers a useful lesson.",
        "Show how careful guidance changes the outcome of a difficult task.",
    ]
    story_qa = [
        QAItem(f"What problem did {params.leader} and {params.helper} face?", lesson["problem_answer"]),
        QAItem("How did supervision improve the team's choice?", lesson["choice_answer"]),
        QAItem("What did the flashback teach the helper?", lesson["memory"]),
        QAItem(f"How did teamwork solve the problem in {title}?", lesson["result_answer"]),
        QAItem("What final image shows that the work succeeded?", f"The story closes with {lesson['ending']}."),
    ]
    world_qa = [
        QAItem("What is supervision?", "Supervision is watching work carefully and offering guidance so people can stay safe and make good choices."),
        QAItem("What is teamwork?", "Teamwork is when people combine their different efforts to reach a shared goal."),
        QAItem("What is a flashback?", "A flashback is a moment in a story that shows something that happened earlier."),
        QAItem("Why can a memory help during a problem?", "A memory can help because an earlier experience may provide a useful idea for the present."),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


ASP_RULES = r"""
setting(hillside_mill).
setting(cedar_bridge).
setting(little_orchard).
feature(supervision).
feature(teamwork).
feature(flashback).
ready(S) :- setting(S), feature(supervision), feature(teamwork), feature(flashback).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for setting in SETTING_REGISTRY:
        lines.append(asp.fact("setting", setting.replace("the ", "").replace(" ", "_")))
    for feature in ("supervision", "teamwork", "flashback"):
        lines.append(asp.fact("feature", feature))
    return "\n".join(lines)


def asp_program(show: str = "#show ready/1.") -> str:
    return asp_facts() + "\n" + ASP_RULES + "\n" + show + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A fable world of supervision, teamwork, and flashback.")
    parser.add_argument("--setting", choices=list(SETTING_REGISTRY))
    parser.add_argument("--leader")
    parser.add_argument("--helper")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    leader = args.leader or rng.choice(["Mara", "Odo", "Nell", "Toma"])
    helper = args.helper or rng.choice(["Pip", "Lio", "Bram", "Suki"])
    if leader == helper:
        raise StoryError("The supervisor and helper must be different characters.")
    return StoryParams(
        setting=args.setting or rng.choice(list(SETTING_REGISTRY)),
        leader=leader,
        helper=helper,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            print(f"{entity.name}: kind={entity.kind}, meters={entity.meters}, memes={entity.memes}")
    if qa:
        print("\n== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def asp_verify() -> int:
    import asp
    expected = {(setting.replace("the ", "").replace(" ", "_"),) for setting in SETTING_REGISTRY}
    model = asp.one_model(asp_program())
    actual = set(asp.atoms(model, "ready"))
    if actual != expected:
        print("MISMATCH between Python and ASP:")
        print("python only:", sorted(expected - actual))
        print("ASP only:", sorted(actual - expected))
        return 1
    for setting in SETTING_REGISTRY:
        sample = generate(StoryParams(setting=setting, leader="Mara", helper="Pip"))
        if not sample.story or "supervision" not in sample.story:
            print("Generated story verification failed.")
            return 1
    print(f"OK: ASP parity and generated stories verified ({len(expected)} settings).")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        for item in sorted(asp.atoms(model, "ready")):
            print(item[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        for setting in SETTING_REGISTRY:
            samples.append(generate(StoryParams(setting=setting, leader="Mara", helper="Pip")))
    else:
        seen = set()
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
