#!/usr/bin/env python3
"""
procrastinate_stub_misunderstanding_sharing_animal_story.py
============================================================

A small Animal Story world about Luna, a procrastinating rabbit, and a stub
that causes a misunderstanding before sharing repairs the friendship.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "animal"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    name: str
    material: str
    consequence: str


@dataclass
class World:
    setting: Setting
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


SETTINGS = {
    "meadow": Setting("the sunny meadow", {"sharing_task"}),
}

TASKS = {
    "sharing_task": Task(
        "sharing_task",
        "sharing task",
        "clover leaves",
        "the little animals will have a shelter before the evening rain",
    ),
}

ANIMALS = ["rabbit", "squirrel", "hedgehog", "mouse", "otter"]
TRAITS = ["curious", "gentle", "cheerful", "careful", "hopeful"]
HELPERS = ["Pip", "Toby", "Nell", "Mara", "Bram"]
SCENARIOS = [
    {
        "id": "twig_pile",
        "opening": "Luna promised to bring three straight twigs for the meadow animals' sharing shelter.",
        "delay": "But Luna decided to look for them after one more game of pebble-hop.",
        "stub": "A short stub of a branch was all she found when the sun began to dip.",
        "misunderstanding": "Pip saw the stub and thought Luna had taken the best twigs for herself.",
        "repair": "Luna explained that she had procrastinated, admitted the truth, and shared her own dry grass while Pip gathered stronger branches.",
        "ending": "The finished shelter stood beneath the old oak, with the stub tucked beside the door as a reminder to begin on time.",
        "lesson": "waiting too long can make a small job harder, but honesty and sharing can still mend a misunderstanding",
    },
    {
        "id": "berry_basket",
        "opening": "Luna was supposed to carry a basket of berries to a picnic where every meadow friend would share.",
        "delay": "She procrastinated by chasing a yellow butterfly instead of checking the basket strap.",
        "stub": "The strap snapped against a branch stub, and several berries rolled into the grass.",
        "misunderstanding": "Mara thought Luna had hidden the berries because she wanted the sweetest ones.",
        "repair": "Luna told Mara what had happened, searched under the leaves, and shared the berries she had saved in her pocket.",
        "ending": "At sunset, each animal held one bright berry while the little stub wore a loop of repaired vine.",
        "lesson": "a clear explanation can turn a hurt guess into a chance to share",
    },
    {
        "id": "painted_sign",
        "opening": "Luna agreed to paint a sign pointing meadow visitors toward the sharing table.",
        "delay": "She procrastinated until the paint grew thick and the afternoon breeze began to blow.",
        "stub": "The sign caught on a branch stub and tore across the word SHARE.",
        "misunderstanding": "Toby thought Luna had covered the sign because she did not want anyone finding the food.",
        "repair": "Luna apologized for waiting, showed Toby the torn place, and shared her blue paint so they could make a new sign together.",
        "ending": "The new sign shone beside the stub, and arrows led every hungry friend toward the same full table.",
        "lesson": "sharing grows stronger when people replace guesses with patient truth",
    },
]


@dataclass
class StoryParams:
    setting: str
    task: str
    name: str
    species: str
    helper: str
    trait: str
    scenario: str = "twig_pile"
    seed: Optional[int] = None
    telling: int = 0


def valid_combos() -> list[tuple[str, str]]:
    return [
        (place, task)
        for place, setting in SETTINGS.items()
        for task in setting.affords
        if task in TASKS
    ]


ASP_RULES = r"""
place(meadow).
affords(meadow,sharing_task).
task(sharing_task).
valid(Place,Task) :- place(Place), affords(Place,Task), task(Task).
#show valid/2.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for place, setting in SETTINGS.items():
        for task in sorted(setting.affords):
            lines.append(asp.fact("affords", place, task))
    for task in TASKS:
        lines.append(asp.fact("task", task))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combinations).")
        return 0
    print("MISMATCH between Python and clingo:")
    print("  only in Python:", sorted(py - clingo))
    print("  only in clingo:", sorted(clingo - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Animal Story world about procrastination, misunderstanding, and sharing."
    )
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--task", choices=TASKS)
    parser.add_argument("--name", default="Luna")
    parser.add_argument("--species", choices=ANIMALS)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--trait", choices=TRAITS)
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
    combos = [
        combo for combo in valid_combos()
        if args.setting is None or combo[0] == args.setting
        if args.task is None or combo[1] == args.task
    ]
    if not combos:
        raise StoryError("No valid setting and task combination matches the requested options.")
    setting, task = rng.choice(combos)
    return StoryParams(
        setting=setting,
        task=task,
        name=args.name or "Luna",
        species=args.species or "rabbit",
        helper=args.helper or rng.choice(HELPERS),
        trait=args.trait or rng.choice(TRAITS),
        scenario=rng.choice(SCENARIOS)["id"],
        telling=rng.randrange(1_000_000),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.task not in TASKS or params.task not in SETTINGS[params.setting].affords:
        raise StoryError(f"Task {params.task!r} is not available in {params.setting!r}.")

    rng = random.Random(params.telling)
    scenario = next(item for item in SCENARIOS if item["id"] == params.scenario)
    setting = SETTINGS[params.setting]
    task = TASKS[params.task]
    world = World(setting)

    hero = world.add(Entity(params.name, type=params.species, label=params.trait))
    helper = world.add(Entity(params.helper, type="animal"))
    hero.meters["unfinished_work"] = 1
    hero.memes["hope"] = 1

    dialogue = rng.choice([
        f'"I thought you were saving the best pieces for yourself," {helper.id} said.',
        f'"Please let me explain," {helper.id} said. "Then we can decide together."',
        f'"I should have told you sooner," {hero.id} admitted.',
        f'"A shared job needs shared words," {helper.id} reminded {hero.id}.',
    ])
    turn = rng.choice([
        "That question made Luna stop defending herself and look closely at what had happened.",
        "For the first time, Luna saw how her delay had made an innocent mistake look selfish.",
        "The misunderstanding loosened when Luna chose the truth instead of a clever excuse.",
        "Luna felt the knot in her chest soften as she understood what Pip had seen.",
    ])

    world.say(
        f"In {setting.place}, {hero.id} the {params.trait} {params.species} agreed to help with the {task.name}."
    )
    world.say(scenario["opening"])
    world.para()
    world.say(scenario["delay"])
    world.say(scenario["stub"])
    world.say(scenario["misunderstanding"])
    world.say(dialogue)
    world.para()
    world.say(f"{turn} {scenario['repair']}")
    world.say(
        f"{hero.id} and {helper.id} worked side by side, passing {task.material} back and forth "
        f"until {task.consequence}."
    )
    world.para()
    world.say(
        f"The misunderstanding did not disappear because of a promise alone; it eased because "
        f"{hero.id} told the truth and made sharing part of the repair."
    )
    world.say(f"{hero.id} learned that {scenario['lesson']}.")
    world.say(scenario["ending"])

    hero.meters["unfinished_work"] = 0
    hero.meters["shared_items"] = 1
    hero.memes.update({"honesty": 1, "kindness": 1, "peace": 1})
    helper.memes.update({"understanding": 1, "peace": 1})

    world.facts = {
        "hero": hero,
        "helper": helper,
        "task": task,
        "scenario": scenario,
        "setting": setting,
        "misunderstanding": scenario["misunderstanding"],
        "repair": scenario["repair"],
        "lesson": scenario["lesson"],
        "ending": scenario["ending"],
        "reconciled": True,
    }

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    return [
        "Write a gentle Animal Story about procrastination, a stub, misunderstanding, and sharing.",
        f"Tell a story in which {hero.id} delays a helpful task and repairs a friendship through honest sharing.",
        "Include a clear dialogue exchange that changes what the animals decide to do.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"]
    helper = facts["helper"]
    return [
        QAItem(
            f"What did {hero.id} procrastinate about?",
            f"{hero.id} procrastinated about the helpful sharing task described in the story, so the work was harder when it finally began.",
        ),
        QAItem(
            f"What caused the misunderstanding between {hero.id} and {helper.id}?",
            f"The stub and the unfinished work made {helper.id} think {hero.id} was keeping the best things for {hero.id} rather than preparing to share.",
        ),
        QAItem(
            f"How did {hero.id} repair the misunderstanding?",
            f"{hero.id} explained what happened, apologized for waiting, and {facts['repair']}",
        ),
        QAItem(
            "What changed at the end?",
            f"The animals worked together and shared what they had. The ending image was this: {facts['ending']}",
        ),
        QAItem(
            f"What lesson did {hero.id} learn?",
            f"{hero.id} learned that {facts['lesson']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does procrastinate mean?",
            "To procrastinate means to delay doing something that needs to be done.",
        ),
        QAItem(
            "What is a stub?",
            "A stub is a short piece left after something longer has been cut, broken, or used.",
        ),
        QAItem(
            "What is a misunderstanding?",
            "A misunderstanding is a mistaken idea about what someone meant or what happened.",
        ),
        QAItem(
            "What does sharing mean?",
            "Sharing means letting other people use, enjoy, or receive part of something with you.",
        ),
        QAItem(
            "Why can honest words help friends?",
            "Honest words can explain what happened, correct a mistaken guess, and help friends choose a kind action.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(f"{entity.id}: {entity.type} meters={meters} memes={memes}")
    lines.append(f"place: {world.setting.place}")
    lines.append("facts: misunderstanding repaired through honest sharing")
    return "\n".join(lines)


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
    StoryParams(
        setting="meadow",
        task="sharing_task",
        name="Luna",
        species="rabbit",
        helper="Pip",
        trait="gentle",
        scenario="twig_pile",
        telling=11,
    ),
    StoryParams(
        setting="meadow",
        task="sharing_task",
        name="Luna",
        species="rabbit",
        helper="Mara",
        trait="curious",
        scenario="berry_basket",
        telling=22,
    ),
    StoryParams(
        setting="meadow",
        task="sharing_task",
        name="Luna",
        species="rabbit",
        helper="Toby",
        trait="hopeful",
        scenario="painted_sign",
        telling=33,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(args.n * 20, 20):
            seed = base_seed + index
            index += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
            params.seed = seed
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
