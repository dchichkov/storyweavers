#!/usr/bin/env python3
"""
A child-facing adventure about maintenance, callaloo, and a marsh in a sandbox.

Luna discovers that the sandbox marsh's tiny water wheel needs maintenance before
the callaloo patch dries out. With a friend, a reed whistle, and a careful repair,
she learns that a small sound can guide a large rescue.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    id: str
    label: str
    affords: set[str]


@dataclass
class Task:
    id: str
    label: str
    needed: list[str]
    payoff: str


@dataclass
class StoryParams:
    place: str
    task: str
    hero: str
    helper: str
    sound: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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


PLACES = {
    "sandbox": Place(
        "sandbox",
        "the sandbox",
        {"marsh", "callaloo", "maintenance"},
    ),
}

TASKS = {
    "water_wheel": Task(
        "water_wheel",
        "repair the marsh water wheel",
        ["twig", "shell", "reed"],
        "the wheel turned again and sent water toward the callaloo",
    ),
    "bridge": Task(
        "bridge",
        "mend the little marsh bridge",
        ["board", "vine", "pebble"],
        "the bridge held firm above the muddy water",
    ),
    "drain": Task(
        "drain",
        "clear the callaloo water channel",
        ["spoon", "leaf", "stone"],
        "fresh water slipped through the channel",
    ),
}

HEROES = ["Luna", "Mara", "Tavi", "Niko"]
HELPERS = ["Pip", "Jo", "Suri", "Bram", "Eli"]
SOUNDS = {
    "whistle": ("FWEET!", "a bright reed whistle"),
    "clap": ("CLAP-CLAP!", "two sharp claps"),
    "drum": ("TUM-TUM!", "a tiny sand-drum beat"),
    "bell": ("TING!", "a little shell bell"),
}

ARCS = {
    "water_wheel": [
        (
            "The sandbox marsh was drying at the edges, and the callaloo leaves drooped like sleepy green hands.",
            "A pebble had jammed the water wheel, while a loose reed pointed toward the hidden repair basket.",
            "The first push made the wheel squeak, then a gust blew the shell washer into the mud.",
            "The hero held the twig steady, the helper searched by sound, and together they fitted the shell and reed into place.",
            "The pointing reed had shown where the basket was, and the sound helped them find the shell after it vanished.",
        ),
        (
            "A warm afternoon had left the sandbox marsh thirsty, but one brave callaloo sprout still stood tall.",
            "The wheel's wooden paddle was crooked, and three tiny scratches marked the safe side of its axle.",
            "A sudden scoop of sand buried the maintenance tools just as the children reached the wheel.",
            "The hero brushed the sand away while the helper counted the scratches and passed each tool in order.",
            "The scratches were a quiet maintenance plan; following them stopped the paddle from being placed backward.",
        ),
    ],
    "bridge": [
        (
            "The marsh path crossed a puddle in the sandbox, and the callaloo basket waited on the far side.",
            "One bridge board wobbled whenever a snail crossed it, making a soft wooden knock.",
            "The board slipped loose when the basket began to roll toward the water.",
            "The hero stopped the basket, the helper looped the vine, and both placed the pebble beneath the board.",
            "The early knock had warned them which board needed maintenance before anyone stepped across.",
        ),
        (
            "Luna's sandbox adventure began when the callaloo patch needed a watering can from across the marsh.",
            "A bridge rail wore a bright line of mud where yesterday's repair had failed.",
            "The rail snapped as the watering can bumped it, and the can tipped toward the marsh.",
            "The hero caught the handle while the helper tied the vine and wedged the board under the rail.",
            "The mud line revealed the weak place, so their repair strengthened the exact spot that had failed.",
        ),
    ],
    "drain": [
        (
            "The callaloo plants in the sandbox had curled their leaves because the marsh channel was clogged.",
            "A spoon-shaped hollow in the sand showed where the last cleaning tool belonged.",
            "When the children pulled the leaf plug, the water bubbled backward with a muddy GLUP!",
            "The hero placed the stone as a stop, and the helper used the spoon to lift the leaf without blocking the channel again.",
            "The hollow had foreshadowed the correct tool, while the stone kept the returning water from undoing their maintenance.",
        ),
        (
            "The little marsh in the sandbox sounded quiet, and quiet water meant thirsty callaloo.",
            "A trail of shiny pebbles led from the blocked drain to a curled leaf.",
            "The first stone they moved released a quick splash that covered the tool pile.",
            "The hero held the leaf back, and the helper chose the flat stone to guide the water away from the tools.",
            "The pebble trail showed where the water wanted to go, so the children changed their repair instead of fighting the flow.",
        ),
    ],
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Adventure storyworld about maintenance, callaloo, and a marsh in a sandbox."
    )
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--task", choices=sorted(TASKS))
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--sound", choices=sorted(SOUNDS))
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


def valid_combos() -> list[tuple[str, str]]:
    return [
        (place_id, task_id)
        for place_id, place in PLACES.items()
        for task_id in TASKS
        if task_id in place.affords
    ]


ASP_RULES = r"""
place(P) :- place_name(P).
task(T) :- task_name(T).
needs(T, I) :- task_item(T, I).
compatible(P, T) :- place(P), task(T), affords(P, T), all_items(T).
all_items(T) :- needs(T, I).
valid_story(P, T) :- compatible(P, T).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place_name", place_id))
        for affordance in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, affordance))
    for task_id, task in TASKS.items():
        lines.append(asp.fact("task_name", task_id))
        for item in task.needed:
            lines.append(asp.fact("task_item", task_id, item))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    try:
        clingo = set(asp_valid_stories())
    except Exception as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    if py == clingo:
        print(f"OK: ASP and Python agree on {len(py)} valid story combinations.")
        return 0
    print("Mismatch between ASP and Python.")
    print("Only in ASP:", sorted(clingo - py))
    print("Only in Python:", sorted(py - clingo))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        pair for pair in valid_combos()
        if args.place is None or pair[0] == args.place
        if args.task is None or pair[1] == args.task
    ]
    if not choices:
        raise StoryError("No valid sandbox story matches the requested place and task.")
    place, task = rng.choice(sorted(choices))
    hero = args.hero or rng.choice(HEROES)
    helper_choices = [name for name in HELPERS if name != hero]
    helper = args.helper or rng.choice(helper_choices)
    if helper == hero:
        raise StoryError("The hero and helper must have different names.")
    sound = args.sound or rng.choice(sorted(SOUNDS))
    return StoryParams(
        place=place,
        task=task,
        hero=hero,
        helper=helper,
        sound=sound,
    )


def make_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    task = TASKS[params.task]
    sound_text, sound_label = SOUNDS[params.sound]
    arc = random.Random(params.seed).choice(ARCS[params.task])

    world = World(place)
    hero = world.add(Entity(params.hero, "character", params.hero))
    helper = world.add(Entity(params.helper, "character", params.helper))
    marsh = world.add(Entity("marsh", "place", "marsh"))
    callaloo = world.add(Entity("callaloo", "plant", "callaloo"))
    tools = [world.add(Entity(item, "tool", item)) for item in task.needed]

    hero.memes["bravery"] = 1.0
    helper.memes["care"] = 1.0
    marsh.meters["water"] = 0.4
    callaloo.meters["thirst"] = 0.8

    premise, clue, obstacle, jobs, turn = arc
    world.facts.update(
        hero=hero,
        helper=helper,
        marsh=marsh,
        callaloo=callaloo,
        task=task,
        tools=tools,
        sound_text=sound_text,
        sound_label=sound_label,
        premise=premise,
        clue=clue,
        obstacle=obstacle,
        jobs=jobs,
        turn=turn,
        resolved=False,
    )

    world.say(
        f"In the sandbox, {params.hero} discovered that the little marsh needed maintenance."
    )
    world.say(premise)
    world.say(
        f"The callaloo needed water, and the job was to {task.label}. "
        f"The repair kit held a {task.needed[0]}, a {task.needed[1]}, and a {task.needed[2]}."
    )
    world.say(clue)

    world.para()
    world.say(
        f'"We can fix it before the callaloo gives up," said {params.hero}. '
        f'"Then let us listen as carefully as we work," said {params.helper}.'
    )
    world.say(obstacle)
    world.say(f"{params.hero} shouted, “{sound_text}” The sound bounced across the marsh.")
    world.say(jobs)

    hero.meters["focus"] = 1.0
    helper.meters["focus"] = 1.0
    world.fired.add("teamwork")
    world.say(
        f"The {sound_label} gave them a shared signal, so each child knew when to pass the next tool."
    )

    world.para()
    world.say(turn)
    world.say(
        f"They tightened the maintenance repair until the {task.needed[0]}, "
        f"{task.needed[1]}, and {task.needed[2]} all held fast."
    )
    marsh.meters["water"] = 1.0
    callaloo.meters["thirst"] = 0.0
    callaloo.memes["hope"] = 1.0
    world.fired.add("repair_complete")
    world.say(f"At once, {task.payoff}.")
    world.say(
        f"The callaloo lifted its leaves, and the sandbox marsh answered with a happy "
        f"{sound_text.lower()} from the children."
    )
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    task: Task = world.facts["task"]
    return [
        "Write a short child-facing Adventure story set in a sandbox.",
        f"Include maintenance, callaloo, and a marsh while showing how two friends {task.label}.",
        f"Use the sound effect {world.facts['sound_text']} as a clue or signal that changes what the characters do.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    task: Task = world.facts["task"]
    return [
        QAItem(
            question=f"Where did {hero.label}'s adventure happen?",
            answer=f"The adventure happened in the sandbox, where a small marsh grew beside the callaloo.",
        ),
        QAItem(
            question="Why did the children need maintenance?",
            answer=f"They needed maintenance because {world.facts['premise'].lower()}",
        ),
        QAItem(
            question=f"Who helped {hero.label}?",
            answer=f"{helper.label} helped {hero.label}, and they shared the repair work instead of working alone.",
        ),
        QAItem(
            question="What did the sound effect do?",
            answer=f"The sound effect {world.facts['sound_text']} became a shared signal, helping the children find or pass the tools at the right time.",
        ),
        QAItem(
            question="How did the early clue matter later?",
            answer=f"The clue mattered because {world.facts['turn']} It guided the final repair.",
        ),
        QAItem(
            question="What showed that the problem was solved?",
            answer=f"{task.payoff.capitalize()}. The callaloo lifted its leaves and the marsh had water again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is maintenance?",
            answer="Maintenance is careful work that keeps something useful, safe, or working well.",
        ),
        QAItem(
            question="What is callaloo?",
            answer="Callaloo is a leafy green plant used as food in many places.",
        ),
        QAItem(
            question="What is a marsh?",
            answer="A marsh is a wet place where shallow water and plants live together.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a written or performed sound that helps a listener imagine an action.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: kind={entity.kind}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    lines.append(f"  resolved: {world.facts.get('resolved', False)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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


CURATED = [
    StoryParams(
        place="sandbox",
        task="water_wheel",
        hero="Luna",
        helper="Pip",
        sound="whistle",
        seed=11,
    ),
    StoryParams(
        place="sandbox",
        task="bridge",
        hero="Mara",
        helper="Jo",
        sound="bell",
        seed=23,
    ),
    StoryParams(
        place="sandbox",
        task="drain",
        hero="Tavi",
        helper="Suri",
        sound="clap",
        seed=37,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        try:
            stories = asp_valid_stories()
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
            sys.exit(1)
        print(f"{len(stories)} valid sandbox stories:")
        for story in stories:
            print(" ", story)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(item) for item in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index + 1)
            try:
                params = resolve_params(args, rng)
            except StoryError as exc:
                print(exc)
                sys.exit(1)
            params.seed = base_seed + index + 1
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
