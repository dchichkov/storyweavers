#!/usr/bin/env python3
"""
A small folk-tale storyworld about a plough, a misunderstanding, and teamwork.
Luna wants to prepare a shared field, but her helper hears the wrong instruction.
The turn comes when they stop blaming one another, listen carefully, and pull the
plough together; the ending shows the field ready for seeds and friendship restored.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
while not os.path.exists(os.path.join(_storyworlds_dir, "results.py")) and os.path.dirname(_storyworlds_dir) != _storyworlds_dir:
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

    def __post_init__(self) -> None:
        self.meters.setdefault("effort", 0.0)
        self.meters.setdefault("mud", 0.0)
        self.meters.setdefault("damage", 0.0)
        self.memes.setdefault("trust", 0.0)
        self.memes.setdefault("worry", 0.0)
        self.memes.setdefault("pride", 0.0)


@dataclass(frozen=True)
class Setting:
    id: str
    place: str
    soil: str
    landmark: str


@dataclass(frozen=True)
class Task:
    id: str
    need: str
    obstacle: str
    instruction: str
    mistaken_instruction: str
    repair: str
    result: str
    celebration: str
    cause_answer: str
    action_answer: str


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
    "hill_field": Setting("hill_field", "the hill field", "soft brown earth", "an old ash tree"),
    "river_meadow": Setting("river_meadow", "the river meadow", "dark, damp earth", "a willow by the water"),
    "orchard_edge": Setting("orchard_edge", "the orchard edge", "rooty earth", "a crooked apple tree"),
}

TASKS = {
    "spring_sowing": Task(
        "spring_sowing",
        "the village needed a long furrow before the spring seeds could be sown",
        "the first row curved toward the vegetable garden",
        "keep the plough pointed at the ash tree",
        "turn the plough toward the ash tree and then stop",
        "stand together at the handles and choose one clear landmark",
        "the new furrow ran straight from the gate to the far stone",
        "the villagers brought baskets of seed and thanked both workers",
        "The village needed a straight furrow before spring seeds could be sown.",
        "They chose one landmark, spoke clearly, and pulled the plough together.",
    ),
    "bean_patch": Task(
        "bean_patch",
        "the bean patch needed a careful furrow before the rain arrived",
        "stones beneath the grass made the plough leap sideways",
        "walk slowly and lift the handles when a stone appears",
        "walk quickly and push the handles down at every stone",
        "listen for the scrape, call out, and lift together",
        "the stones were cleared and the furrow stayed gentle and even",
        "the children planted beans along the quiet brown line",
        "The bean patch needed a careful furrow before rain arrived.",
        "They called out at each stone and lifted the plough together.",
    ),
    "moon_turnip": Task(
        "moon_turnip",
        "the widow's turnips needed one last furrow before moonrise",
        "long shadows made the field markers look like different shapes",
        "follow the white ribbon tied to the fence post",
        "follow the dark shadow beside the fence post",
        "tie a bright ribbon where both workers could see it",
        "the furrow reached the fence before the moon climbed high",
        "the widow shared warm oat cakes beneath the silver sky",
        "The widow's turnips needed one last furrow before moonrise.",
        "They tied a bright ribbon to a shared marker and followed it together.",
    ),
    "thirsty_garden": Task(
        "thirsty_garden",
        "the village garden needed rows for thirsty pumpkin seeds",
        "the dry soil cracked whenever the plough moved too fast",
        "pull gently and pause when the earth crumbles",
        "pull hard and hurry before the soil grows harder",
        "match their pace and let the plough rest between rows",
        "the soil opened in smooth lines ready for pumpkin seeds",
        "the gardener poured cool water into two wooden cups",
        "The garden needed gentle rows for pumpkin seeds in dry soil.",
        "They matched their pace and let the plough rest between rows.",
    ),
}

NAMES = ["Luna", "Mara", "Tavi", "Nell", "Oren", "Pia"]
HELPERS = ["Bram", "Sela", "Ivo", "Mira", "Tomas", "Faye"]
TRAITS = ["patient", "brave", "cheerful", "thoughtful", "sturdy"]

ASP_RULES = r"""
% A task is suitable when its field and plough are both available.
available(plough).
suitable(T) :- task(T), available(plough).

% Teamwork repairs a misunderstanding when both workers share one marker.
repairable(T) :- suitable(T), shared_marker(T).
valid_scenario(S, T) :- setting(S), task(T), repairable(T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("shared_marker", tid))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_scenario/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [(sid, tid) for sid in SETTINGS for tid in TASKS]


def asp_valid() -> set[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "valid_scenario"))


@dataclass
class StoryParams:
    place: str
    task: str
    hero: str
    helper: str
    trait: str
    opening: int = 0
    turn: int = 0
    ending: int = 0
    seed: Optional[int] = None


def build_world(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown field setting: {params.place}")
    if params.task not in TASKS:
        raise StoryError(f"Unknown plough task: {params.task}")
    if params.hero == params.helper:
        raise StoryError("Teamwork requires two different workers.")
    if params.trait not in TRAITS:
        raise StoryError(f"Unknown character trait: {params.trait}")

    setting = SETTINGS[params.place]
    task = TASKS[params.task]
    world = World(setting)
    hero = world.add(Entity(params.hero, "person", params.hero))
    helper = world.add(Entity(params.helper, "person", params.helper))
    plough = world.add(Entity("plough", "tool", "the wooden plough"))
    field = world.add(Entity("field", "place", setting.place))
    world.facts.update(hero=hero, helper=helper, plough=plough, field=field, task=task)

    openings = [
        f"{hero.label} was a {params.trait} farmer who lived beside {setting.place}. One spring morning, {hero.label} carried the wooden plough to the field, where {helper.label} was waiting beside {setting.landmark}.",
        f"In the village of red roofs, {hero.label} and {helper.label} were asked to guide the plough across {setting.place}. The {params.trait} {hero.label} promised that the work would be done before the first bird finished its song.",
        f"Long ago, {setting.place} belonged to everyone in the village. {hero.label}, a {params.trait} young farmer, brought a sturdy plough, and {helper.label} came to lend a hand.",
        f"At dawn, {hero.label} found {helper.label} beside the plough at {setting.place}. Dew shone on the grass, and the villagers watched from the road, hoping the two friends could prepare the earth together.",
    ]
    world.say(openings[params.opening % len(openings)])
    world.say(f"The task was important: {task.need}.")
    world.para()

    world.say(f"{hero.label} pointed toward {setting.landmark} and said, 'Follow that marker while I guide the plough.'")
    world.say(f"{helper.label} heard the words differently. 'You said to turn toward the marker and stop there,' {helper.label} replied.")
    world.say(f"Because of the misunderstanding, {task.obstacle}. The plough bumped sideways, and a crooked line appeared in the earth.")
    hero.memes["worry"] += 1
    helper.memes["worry"] += 1
    plough.meters["mud"] += 1
    world.para()

    turns = [
        f"{hero.label} took a breath. 'Let us say it plainly. I will hold the handles, and you will call the path.'",
        f"{helper.label} knelt beside the crooked line. 'I heard the wrong thing. Show me one marker we can both see.'",
        f"The two farmers stopped arguing and looked closely at the field. Then {hero.label} said, 'Words are seeds too; we must plant them clearly.'",
        f"{hero.label} and {helper.label} set down their pride. They agreed that the plough would move only when both voices were ready.",
    ]
    world.say(turns[params.turn % len(turns)])
    world.say(f"Together, they chose the safest plan: {task.repair}.")
    world.say(f"{hero.label} called, 'Ready?' 'Ready,' answered {helper.label}. They pulled the plough side by side.")
    hero.meters["effort"] += 1
    helper.meters["effort"] += 1
    hero.memes["trust"] += 1
    helper.memes["trust"] += 1
    plough.meters["mud"] += 1
    if params.turn % 2:
        world.say(f"They moved slowly, listened for one another, and {task.result}.")
    else:
        world.say(f"Each time the earth tugged, one friend called and the other answered; soon {task.result}.")
    world.para()

    endings = [
        f"At sunset, {task.celebration}. {hero.label} and {helper.label} smiled at the straight furrow, knowing that clear words had made their teamwork strong.",
        f"When the first stars appeared, {task.celebration}. The plough rested by {setting.landmark}, clean enough to shine with the last light.",
        f"The villagers came to see the work. {task.celebration}. From then on, {hero.label} and {helper.label} repeated every plan before beginning.",
        f"By evening, {task.celebration}. The crooked first line remained as a small reminder: even good friends must listen carefully.",
    ]
    world.say(endings[params.ending % len(endings)])
    hero.memes["pride"] += 1
    helper.memes["pride"] += 1
    return world


def prompts(world: World) -> list[str]:
    task: Task = world.facts["task"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    return [
        f"Tell a folk tale about {hero.label} using a plough when {task.need}.",
        f"Write a child-friendly story about teamwork and a misunderstanding in {world.setting.place}.",
        "Create a gentle folk tale where two farmers solve a problem by listening and working together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    task: Task = world.facts["task"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    return [
        QAItem("What did the farmers need to do?", task.cause_answer),
        QAItem(
            f"What misunderstanding happened between {hero.label} and {helper.label}?",
            f"{hero.label} meant for {helper.label} to follow one marker, but {helper.label} thought the plough should turn and stop there.",
        ),
        QAItem("How did the farmers fix the problem?", task.action_answer),
        QAItem("What showed that their teamwork succeeded?", f"Their teamwork succeeded because {task.result}."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a plough?", "A plough is a farm tool used to turn and loosen soil so seeds can be planted."),
        QAItem("What is teamwork?", "Teamwork is when people share a task, listen to one another, and work toward the same goal."),
        QAItem("What is a misunderstanding?", "A misunderstanding is when someone hears or understands a message differently from what was meant."),
        QAItem("Why is clear speech helpful?", "Clear speech helps people make the same plan and avoid mistakes."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Folk tale storyworld about a plough, teamwork, and a misunderstanding.")
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--task", choices=sorted(TASKS))
    parser.add_argument("--hero")
    parser.add_argument("--helper")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [combo for combo in combos if combo[0] == args.place]
    if args.task:
        combos = [combo for combo in combos if combo[1] == args.task]
    if not combos:
        raise StoryError("No valid scenario matches the requested place and task.")
    place, task = rng.choice(combos)
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([name for name in HELPERS if name != hero])
    return StoryParams(
        place=place,
        task=task,
        hero=hero,
        helper=helper,
        trait=args.trait or rng.choice(TRAITS),
        opening=rng.randrange(4),
        turn=rng.randrange(4),
        ending=rng.randrange(4),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"setting: {world.setting.place}")
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(f"{entity.label}: meters={meters} memes={memes}")
    return "\n".join(lines)


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = asp_valid()
    if python_set == asp_set:
        print(f"OK: ASP and Python agree on {len(python_set)} valid scenarios.")
        return 0
    print("Mismatch between ASP and Python:")
    print("Only Python:", sorted(python_set - asp_set))
    print("Only ASP:", sorted(asp_set - python_set))
    return 1


def verify_stories() -> int:
    for params in [
        StoryParams("hill_field", "spring_sowing", "Luna", "Bram", "patient"),
        StoryParams("river_meadow", "bean_patch", "Mara", "Sela", "brave", 1, 1, 1),
        StoryParams("orchard_edge", "moon_turnip", "Tavi", "Ivo", "thoughtful", 2, 2, 2),
    ]:
        sample = generate(params)
        if not sample.story or "plough" not in sample.story or not sample.story_qa:
            print("Story verification failed.")
            return 1
    return asp_verify()


CURATED = [
    StoryParams("hill_field", "spring_sowing", "Luna", "Bram", "patient", 0, 0, 0),
    StoryParams("river_meadow", "bean_patch", "Mara", "Sela", "brave", 1, 1, 1),
    StoryParams("orchard_edge", "moon_turnip", "Tavi", "Ivo", "thoughtful", 2, 2, 2),
    StoryParams("hill_field", "thirsty_garden", "Nell", "Mira", "cheerful", 3, 3, 3),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp or args.asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(verify_stories())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        for index in range(max(args.n, 1) * 100):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
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
