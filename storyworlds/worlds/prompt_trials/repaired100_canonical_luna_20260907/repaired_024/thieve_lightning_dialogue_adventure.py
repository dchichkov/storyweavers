#!/usr/bin/env python3
"""
A child-facing adventure about thieving lightning and learning to return it.

Luna follows a bright thief into a storm tower, but a conversation changes the
plan: the stolen lightning is not treasure. It is a frightened creature that
needs a safe path home.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "storyworlds" / "results.py").is_file()
)
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
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


@dataclass
class StoryParams:
    name: str
    place: str
    weather: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Adventure:
    id: str
    tower: str
    clue: str
    danger: str
    helper: str
    warning: str
    stolen_image: str
    return_action: str
    final_image: str
    lesson: str


SETTINGS = {
    "Cloudstep Hill": "the old storm tower",
    "Whispering Moor": "the bell tower beside the moor",
    "Brightwater Cliffs": "the lighthouse tower above the sea",
}

WEATHERS = ["a silver rain", "a warm wind", "a sky full of rolling clouds"]
NAMES = ["Luna", "Mara", "Nia", "Pip", "Tavi", "Orin"]

ADVENTURES = [
    Adventure(
        "blue_arc",
        "old storm tower",
        "a blue spark twitching inside a cracked lantern",
        "the iron stairs shook whenever thunder spoke",
        "a small storm swallow",
        "That lightning was caught, not owned. Ask it where it wants to go.",
        "The lightning curled like a bright fox and hid behind the bell.",
        "opened the tower shutters and guided the spark along the copper rod",
        "The storm swallow flew beside Luna while the lightning leaped safely into the clouds.",
        "bravery is strongest when it protects instead of takes",
    ),
    Adventure(
        "golden_bolt",
        "bell tower beside the moor",
        "a golden bolt trapped in a glass jar",
        "the jar warmed until its stopper began to dance",
        "an old tower keeper",
        "A thief may carry light away, but a friend carries it home.",
        "The bolt flashed against the glass, making tiny pictures of thirsty clouds.",
        "removed the stopper and held the jar beneath the tower's lightning chain",
        "Rain softened the moor, and the golden bolt stitched a bright line through the clouds.",
        "a shiny prize can still belong to someone else",
    ),
    Adventure(
        "green_flash",
        "lighthouse tower above the sea",
        "a green lightning thread tangled in the lighthouse gears",
        "the turning gears pulled the thread toward the dark sea",
        "a talking gull",
        "Do not thieve the storm's path. Give it a clear way through.",
        "The lightning whispered in clicks, and the gull understood every one.",
        "stopped the gears and turned the lighthouse mirror toward the open sky",
        "The sea shone green for one heartbeat before the lightning sailed back to the storm.",
        "listening can reveal the safest adventure",
    ),
]

OPENINGS = [
    "At sunset",
    "Before breakfast",
    "Just as the first cloud covered the moon",
    "When the far hills began to rumble",
]

REQUESTS = [
    "Can we follow the light without hurting it?",
    "What if the lightning is lost?",
    "May I help it find the storm?",
    "Could a thief really steal a piece of thunder?",
]

ASP_RULES = r"""
hero(luna).
lightning(stolen).
dialogue(heard).
danger(stairs).
returns_home(luna) :- lightning(stolen), dialogue(heard), danger(stairs).
safe_ending :- returns_home(luna).
#show returns_home/1.
#show safe_ending/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero", "luna"),
        asp.fact("lightning", "stolen"),
        asp.fact("dialogue", "heard"),
        asp.fact("danger", "stairs"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show safe_ending/0."))
    if any(atom.name == "safe_ending" for atom in model):
        print("OK: ASP predicts a safe ending.")
        return 0
    print("MISMATCH: ASP did not predict a safe ending.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="An adventure about thieving lightning and a brave return."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--weather", choices=WEATHERS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        place=args.place or rng.choice(list(SETTINGS)),
        weather=args.weather or rng.choice(WEATHERS),
        seed=args.seed,
    )


def choose_adventure(seed: int) -> Adventure:
    return ADVENTURES[seed % len(ADVENTURES)]


def tell(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.weather not in WEATHERS:
        raise StoryError(f"Unknown weather: {params.weather}")

    seed = params.seed
    if seed is None:
        seed = sum(ord(c) for c in f"{params.name}|{params.place}|{params.weather}")
    adventure = choose_adventure(seed)
    opening = OPENINGS[(seed // 3) % len(OPENINGS)]
    request = REQUESTS[(seed // 7) % len(REQUESTS)]

    world = World()
    hero = world.add(Entity("hero", "child", params.name, memes={"courage": 1}))
    lightning = world.add(Entity(
        "lightning", "storm_light", "the stolen lightning",
        meters={"trapped": 1, "danger": 1},
        memes={"fear": 1},
        owner="storm",
    ))
    tower = world.add(Entity("tower", "place", adventure.tower))
    helper = world.add(Entity("helper", "helper", adventure.helper))
    world.facts.update(
        hero=hero,
        lightning=lightning,
        tower=tower,
        helper=helper,
        adventure=adventure,
        place=params.place,
        weather=params.weather,
        request=request,
    )

    world.say(
        f"{opening}, {params.name} climbed {SETTINGS[params.place]} through {params.weather}."
    )
    world.say(
        f"At the top, {params.name} saw {adventure.clue}. The bright thing had been thieved from the storm."
    )

    world.para()
    lightning.memes["fear"] = 2
    world.say(
        f"The lightning trembled inside the tower, and the iron stairs shook whenever thunder spoke."
    )
    world.say(
        f"A {adventure.helper} appeared beside the doorway. \"{adventure.warning}\""
    )
    world.say(f"\"{request}\" {params.name} asked.")
    world.say(
        f"\"Then listen before you act,\" said the {adventure.helper}. "
        f"\"It may be asking for help.\""
    )

    world.para()
    world.say(
        f"{params.name} leaned close. {adventure.stolen_image}"
    )
    world.say(
        f"The frightened lightning answered with a soft crackle, pointing toward the open sky."
    )
    world.say(
        f"\"I thought I was taking a treasure,\" {params.name} said. "
        f"\"I will not thieve you again.\""
    )
    world.say(
        f"\"Good,\" replied the {adventure.helper}. \"A promise needs an action.\""
    )

    lightning.meters["trapped"] = 0
    lightning.meters["returned"] = 1
    lightning.memes["fear"] = 0
    hero.meters["chose_help"] = 1
    world.fired.add("dialogue_changed_plan")
    world.say(f"{params.name} {adventure.return_action}.")

    world.para()
    world.say(
        f"The tower grew still. The lightning rushed upward, and the clouds answered with a deep, happy roll."
    )
    world.say(adventure.final_image)
    world.say(
        f"{params.name} understood that {adventure.lesson}."
    )
    world.facts["safe_ending"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    adventure = world.facts["adventure"]
    return [
        f"Write an adventure about {world.facts['hero'].label} discovering thieved lightning in {world.facts['place']}.",
        f"Include a dialogue in which a helper says: \"{adventure.warning}\"",
        f"Show the lightning returning safely after {world.facts['hero'].label} learns that {adventure.lesson}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    lightning = world.facts["lightning"]
    adventure = world.facts["adventure"]
    return [
        QAItem(
            "Who found the thieved lightning?",
            f"{hero.label} found the thieved lightning in {world.facts['tower'].label}.",
        ),
        QAItem(
            "Why was the lightning in danger?",
            f"The lightning was trapped in the tower and frightened by the shaking stairs and storm.",
        ),
        QAItem(
            "How did dialogue change the adventure?",
            f"The helper told {hero.label} to listen to the lightning, so {hero.label} stopped treating it like a treasure and chose to return it.",
        ),
        QAItem(
            "How did the story end?",
            f"{hero.label} {adventure.return_action}, and the lightning returned safely to the storm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is lightning?",
            "Lightning is a bright electrical flash that happens during a storm.",
        ),
        QAItem(
            "What does it mean to thieve something?",
            "To thieve something means to take it secretly when it belongs to someone else.",
        ),
        QAItem(
            "Why is dialogue useful in an adventure?",
            "Dialogue lets characters share warnings and ideas that can change what they decide to do.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: {entity.type} {entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


CURATED = [
    StoryParams("Luna", "Cloudstep Hill", "a silver rain", 11),
    StoryParams("Mara", "Whispering Moor", "a warm wind", 22),
    StoryParams("Nia", "Brightwater Cliffs", "a sky full of rolling clouds", 33),
]


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show safe_ending/0."))
        print("safe ending:", any(atom.name == "safe_ending" for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
        for index in range(max(0, args.n)):
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
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
