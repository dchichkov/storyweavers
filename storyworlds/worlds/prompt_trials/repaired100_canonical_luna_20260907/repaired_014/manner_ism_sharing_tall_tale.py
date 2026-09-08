#!/usr/bin/env python3
"""
A small tall tale about a manner-ism, a shared task, and a moon-sized lesson.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
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
class Setting:
    name: str
    affords: set[str] = field(default_factory=lambda: {"share", "carry", "listen"})


@dataclass
class StoryParams:
    child_name: str
    helper_name: str
    elder_name: str
    place: int = 0
    task: int = 0
    manner: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Tale:
    place: str
    object_name: str
    object_plural: str
    trouble: str
    first_attempt: str
    shared_method: str
    enormous_result: str
    ending: str


TALES = [
    Tale(
        "the valley of Whistling Hills",
        "a silver spoon",
        "silver spoons",
        "the village needed one spoon to stir a kettle big enough to bathe an elephant",
        "lifted the spoon alone, but it would not budge",
        "passed the spoon from hand to hand while everyone counted together",
        "the spoon leaped up and stirred the kettle so fast that the steam made a new cloud",
        "the cloud rained warm soup over every hungry roof",
    ),
    Tale(
        "the windy town of Belltop",
        "a blue ribbon",
        "blue ribbons",
        "the town's giant parade kite had tangled itself around the tallest bell tower",
        "tugged the ribbon with all his strength, but the kite only sneezed",
        "shared the pulling, knot-checking, and cheering among the whole parade",
        "the kite rose higher than the sunrise and tickled the moon",
        "the moon wore the ribbon as a shining belt that night",
    ),
    Tale(
        "the orchard beyond Seven Bridges",
        "a golden ladder",
        "golden ladders",
        "one ladder had to reach an apple hanging above the clouds",
        "climbed three steps before the ladder wobbled like pudding",
        "shared the rungs, held the feet, and picked one apple for every helper",
        "the ladder stretched straight up and touched the cloud",
        "the apple became a pie large enough for the entire orchard",
    ),
    Tale(
        "the red desert of Long Echo",
        "a striped umbrella",
        "striped umbrellas",
        "the sun had grown so hot that the town's shadow was hiding under a rock",
        "opened the umbrella alone, but the wind turned it inside out",
        "shared the handle, the corners, and the job of watching the wind",
        "the umbrella spread wider than a barn",
        "the grateful shadow came home and rested over the town",
    ),
]


MANNERS = [
    ("tipping his hat before asking", "A polite beginning made every helper feel welcome."),
    ("saying please before each request", "The small word opened more hands than the biggest bell."),
    ("waiting for each person to finish speaking", "Listening let the team discover the best order for the work."),
    ("offering the first turn to someone else", "A generous first turn made sharing feel fair."),
]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

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


def build_story(params: StoryParams) -> World:
    if not params.child_name.strip() or not params.helper_name.strip():
        raise StoryError("child and helper names must not be empty")
    if params.child_name.strip().lower() == params.helper_name.strip().lower():
        raise StoryError("child and helper must have different names")

    tale = TALES[params.place % len(TALES)]
    manner, meaning = MANNERS[params.manner % len(MANNERS)]
    setting = Setting(tale.place)
    world = World(setting)

    child = world.add(Entity("Child", "character", "child", params.child_name))
    helper = world.add(Entity("Helper", "character", "child", params.helper_name))
    elder = world.add(Entity("Elder", "character", "adult", params.elder_name))
    object_entity = world.add(Entity("SharedObject", "thing", "object", tale.object_name))

    world.facts.update(
        child=child,
        helper=helper,
        elder=elder,
        object=object_entity,
        tale=tale,
        manner=manner,
        meaning=meaning,
        shares=0,
    )

    world.say(
        f"In {setting.name}, {child.label} was famous for one enormous manner-ism: {manner}."
    )
    world.say(
        f"One morning, {tale.trouble.capitalize()}. "
        f"{child.label} declared, \"I can fix it!\""
    )
    child.memes["confidence"] = 1.0
    object_entity.meters["weight"] = 10.0

    world.para()
    world.say(
        f"{child.label} {tale.first_attempt}, and the ground gave a mighty wobble."
    )
    world.say(
        f"{helper.label} called, \"Please let us share the work.\" "
        f"{child.label} answered, \"You are right. We can make one giant team.\""
    )
    helper.memes["wisdom"] = 1.0
    child.memes["cooperation"] = 1.0
    world.facts["shares"] = 1

    world.para()
    world.say(
        f"First, {child.label} {manner}. Then {helper.label} explained how to share the jobs."
    )
    world.say(f"They {tale.shared_method}.")
    world.say(
        f"\"Sharing is not giving away the whole job,\" said {helper.label}. "
        "\"It is giving everyone a useful part.\""
    )
    world.facts["shares"] = 2
    object_entity.meters["supported"] = 1.0

    world.para()
    world.say(
        f"When {elder.label} joined them, the team grew as tall as a tower. "
        f"Their shared effort meant that {tale.enormous_result}."
    )
    object_entity.meters["lifted"] = 1.0
    world.say(
        f"{child.label} laughed. \"My manner-ism helped me ask politely, but sharing helped us finish.\""
    )
    world.say(
        f"{helper.label} nodded. \"And everyone gets to enjoy the result.\""
    )
    world.facts["shares"] = 3

    world.para()
    world.say(
        f"By sunset, {tale.ending}. "
        f"{child.label} still tipped his hat before asking, but now he always made room for another pair of hands."
    )
    world.facts["lesson"] = "Polite manners invite help, and sharing makes a huge task possible."
    return world


def generation_prompts(world: World) -> list[str]:
    tale: Tale = world.facts["tale"]  # type: ignore[assignment]
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    return [
        f"Write a tall tale about {child.label} using a manner-ism to solve a gigantic problem in {world.setting.name}.",
        f"Tell a child-friendly story where sharing {tale.object_name} helps many characters accomplish an impossible task.",
        "Write a humorous tall tale with a clear lesson about polite manners and sharing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    tale: Tale = world.facts["tale"]  # type: ignore[assignment]
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    return [
        QAItem(
            f"What manner-ism did {child.label} use?",
            f"{child.label} used the manner-ism of {world.facts['manner']}.",
        ),
        QAItem(
            f"Why could {child.label} not solve the problem alone?",
            f"The task was enormous: {tale.trouble}. One person could not manage it safely alone.",
        ),
        QAItem(
            f"How did {child.label} and {helper.label} solve the problem?",
            f"They shared the work by {tale.shared_method}. Each person handled a useful part.",
        ),
        QAItem(
            "What lesson did the tall tale teach?",
            f"It taught that polite manners invite help, while sharing makes a huge task possible. The team proved this when {tale.enormous_result}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a manner-ism?",
            "A manner-ism is a noticeable way someone behaves or does something, such as tipping a hat or saying please.",
        ),
        QAItem(
            "What does sharing mean?",
            "Sharing means giving other people a fair chance to use something or take part in a task.",
        ),
        QAItem(
            "What is a tall tale?",
            "A tall tale is a playful story that exaggerates events to impossible, funny, or astonishing sizes.",
        ),
        QAItem(
            "Why can sharing help with a difficult task?",
            "Sharing divides a difficult task into useful parts, so many people can contribute instead of one person doing everything.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:12} ({entity.type:8}) meters={meters} memes={memes}"
        )
    lines.append(f"  shared_work={world.facts.get('shares', 0)}")
    lines.append(f"  setting={world.setting.name}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("topic", "manner_ism"),
            asp.fact("feature", "sharing"),
            asp.fact("style", "tall_tale"),
            asp.fact("action", "ask_politely"),
            asp.fact("action", "share_work"),
            asp.fact("setting", "impossible_place"),
        ]
    )


ASP_RULES = r"""
topic(manner_ism).
feature(sharing).
style(tall_tale).
action(ask_politely).
action(share_work).
setting(impossible_place).

invites_help(manner_ism) :- action(ask_politely), topic(manner_ism).
task_possible(sharing) :- action(share_work), feature(sharing).
story_ok :- invites_help(manner_ism), task_possible(sharing), style(tall_tale),
            setting(impossible_place).
#show story_ok/0.
"""


def asp_program(show: str = "#show story_ok/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    ok = any(symbol.name == "story_ok" for symbol in model)
    if not ok:
        print("MISMATCH: ASP twin failed.")
        return 1
    for params in (
        StoryParams("Luna", "Mara", "Grandpa Sol"),
        StoryParams("Pip", "Nia", "Aunt Fern", place=2, manner=3),
    ):
        sample = generate(params)
        if "sharing" not in sample.story.lower():
            print("MISMATCH: generated story omitted sharing.")
            return 1
        if "manner" not in sample.story.lower():
            print("MISMATCH: generated story omitted manner-ism.")
            return 1
    print("OK: ASP twin and generated stories agree.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A tall tale about manner-ism, sharing, and a very large task."
    )
    parser.add_argument("--child-name")
    parser.add_argument("--helper-name")
    parser.add_argument("--elder-name")
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


CHILD_NAMES = ["Luna", "Pip", "Milo", "Tess", "Ollie", "Nell"]
HELPER_NAMES = ["Mara", "Nia", "Bea", "Ravi", "Cleo", "Finn"]
ELDER_NAMES = ["Grandpa Sol", "Aunt Fern", "Uncle Jo", "Grandma Ada"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child = args.child_name or rng.choice(CHILD_NAMES)
    helper = args.helper_name or rng.choice(HELPER_NAMES)
    elder = args.elder_name or rng.choice(ELDER_NAMES)
    if child.lower() == helper.lower():
        helper = next(name for name in HELPER_NAMES if name.lower() != child.lower())
    return StoryParams(
        child_name=child,
        helper_name=helper,
        elder_name=elder,
        place=rng.randrange(len(TALES)),
        task=rng.randrange(len(TALES)),
        manner=rng.randrange(len(MANNERS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
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
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("story_ok" if any(symbol.name == "story_ok" for symbol in model) else "no model")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index in range(len(TALES)):
            params = StoryParams(
                child_name="Luna",
                helper_name="Mara",
                elder_name="Grandpa Sol",
                place=index,
                task=index,
                manner=index % len(MANNERS),
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < max(0, args.n) and attempts < max(20, args.n * 20):
            rng = random.Random(base_seed + attempts)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempts
            sample = generate(params)
            attempts += 1
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
