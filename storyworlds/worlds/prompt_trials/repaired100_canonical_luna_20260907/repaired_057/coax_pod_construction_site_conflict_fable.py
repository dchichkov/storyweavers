#!/usr/bin/env python3
"""
A small fable-like story world at a construction site, where coaxing helps
resolve a conflict about a little pod.
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
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "the construction site"
    safety: str = "behind the striped safety fence"
    affords: set[str] = field(default_factory=lambda: {"build", "listen", "coax", "share"})


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    object_name: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    title: str
    opening: str
    conflict: str
    first_try: str
    clue: str
    coax_method: str
    helper_action: str
    discovery: str
    resolution: str
    lesson: str
    ending: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


SETTING = Setting()

HERO_NAMES = ["Luna", "Milo", "Nell", "Pip", "Tara", "Bram", "Ivy", "Oren"]
HELPER_NAMES = ["Sage", "Wren", "Kit", "Penny", "Jo", "Finn", "Mara", "Theo"]

OBJECTS = {
    "pod": {
        "label": "pod",
        "phrase": "a small green pod",
        "type": "seed_pod",
    }
}

SCENARIOS = (
    Scenario(
        "the wedged pod",
        "Morning clanged with hammers and cheerful trucks",
        "a little green pod had rolled beneath a stack of wooden boards",
        "pulled the nearest board with all their might, but the stack only groaned",
        "the pod trembled whenever the loud crane moved",
        "a soft song and a gentle tap on the board",
        "held a cardboard shade near the pod while the builder lifted one board safely",
        "the pod was not stuck in the dirt; it was resting against a loose red brick",
        "moved the brick, carried the pod to the garden corner, and marked the safe path around the boards",
        "a hard push may make a quarrel, but patient coaxing can invite things to move",
        "By sunset, the pod rested in warm soil, and a tiny green curl pointed toward the sky",
    ),
    Scenario(
        "the noisy pod",
        "the new library wall rose beside a busy cement mixer",
        "a round pod had rolled into a tin bucket, and every rumble made it spin",
        "shook the bucket to make the pod come out, but the spinning only grew faster",
        "the pod stopped whenever the mixer stopped",
        "a quiet pause, a kind voice, and a tilted cloth ramp",
        "asked the driver for one safe still moment and held the ramp steady",
        "the pod followed the ramp when the bucket was calm",
        "guided the pod into a padded box and returned the bucket to the tool table",
        "listening for the right moment is wiser than fighting every noisy problem",
        "The mixer rested at dusk, while the pod slept in its box like a small green moon",
    ),
    Scenario(
        "the guarded pod",
        "the builders had set a bright orange cone beside a fresh path",
        "a young crow guarded a pod near the cone and pecked at anyone who came close",
        "waved a glove to shoo the crow away, but the crow flapped and cried",
        "the crow flew only to a nearby beam and watched the pod from there",
        "a slow retreat, a handful of safe crumbs, and a calm invitation",
        "placed crumbs well away from the work area while the foreman waited",
        "the crow wanted the shiny wrapper beside the pod, not the pod itself",
        "removed the wrapper, let the crow collect it, and carried the pod to the sheltered garden bed",
        "understanding another creature's worry can end a conflict better than chasing",
        "The crow returned to the beam, and the pod lay safe beneath a little sign: Grow gently",
    ),
    Scenario(
        "the rope-line pod",
        "fresh ropes marked the safe walking lane through the site",
        "a pod had caught on the rope, while a wheelbarrow worker and a painter argued about who should move it",
        "tugged the rope from one side, but both workers shouted that the lane must not shift",
        "the rope knot was tied around a smooth hook, not around the pod",
        "a careful question and a shared count to three",
        "asked both workers to hold the rope while the site guide loosened the hook",
        "the pod slipped free without moving the safety lane",
        "placed the pod in a tray and thanked both workers for protecting the path",
        "a calm question can turn two sides of a quarrel toward one safe answer",
        "The lane stayed straight, and the rescued pod rode home in the tray",
    ),
    Scenario(
        "the rain-puddle pod",
        "a silver rain had filled the shallow hollows near the unfinished porch",
        "a pod floated toward a drain, while a little cart blocked the easiest approach",
        "pushed the cart quickly, but its wheels sank deeper into the soft ground",
        "a narrow plank made a dry bridge beside the cart",
        "a gentle plan, a dry plank, and a promise to wait",
        "held the plank while the site worker moved the cart with a proper handle",
        "the pod drifted into a quiet puddle away from the drain",
        "scooped it into a cup and placed it beneath the porch roof",
        "when a plan fails, coaxing the right help is stronger than forcing the wrong tool",
        "Rain tapped the roof, and the pod rested in its cup until the clouds went home",
    ),
)

ASP_RULES = r"""
item(pod).
at(pod, construction_site).
conflict(pod).
curious(hero).
helper(helper).
coaxing(hero).
safe_method(coaxing).
resolved(conflict) :- conflict(pod), coaxing(hero), helper(helper), safe_method(coaxing).
happy_end :- resolved(conflict).
"""

SCENARIO_LINES = (
    "'Let us not fight the problem,' said {helper}. 'Let us coax it toward a safe way.'",
    "{hero} said, 'I wanted to fix it quickly, but perhaps your careful idea can help.'",
    "'A gentle word first,' said {helper}. 'Then we can ask the grown-ups for the right tool.'",
    "{hero} took a breath. 'Will you help me listen before I try again?'",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Construction-site coax-and-pod fable world.")
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--object", dest="object_name", choices=sorted(OBJECTS))
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--helper-gender", choices=["girl", "boy"])
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
    hero_type = args.gender or rng.choice(["girl", "boy"])
    helper_type = args.helper_gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice([name for name in HELPER_NAMES if name != hero_name])
    object_name = args.object_name or "pod"
    if object_name not in OBJECTS:
        raise StoryError("This story world only knows about the pod.")
    if hero_name == helper_name:
        raise StoryError("The hero and helper must have different names.")
    return StoryParams(hero_name, hero_type, helper_name, helper_type, object_name)


def scenario_for(params: StoryParams) -> Scenario:
    value = params.seed
    if value is None:
        value = sum((index + 1) * ord(char) for index, char in enumerate(params.hero_name + params.helper_name))
    return SCENARIOS[value % len(SCENARIOS)]


def make_world(params: StoryParams) -> World:
    world = World(SETTING)
    world.add(Entity("hero", params.hero_type, params.hero_name))
    world.add(Entity("helper", params.helper_type, params.helper_name))
    world.add(Entity("pod", "seed_pod", OBJECTS[params.object_name]["label"]))
    return world


def tell_story(params: StoryParams) -> World:
    world = make_world(params)
    scenario = scenario_for(params)
    hero = world.entities["hero"]
    helper = world.entities["helper"]
    pod = world.entities["pod"]

    world.say(f"At {SETTING.place}, {hero.label} worked {SETTING.safety} with {helper.label}.")
    world.say(f"{scenario.opening}. But {scenario.conflict}.")
    world.say(
        f"{hero.label} spotted {OBJECTS[params.object_name]['phrase']} and wanted to help. "
        f"'I can fix this,' {hero.label} said."
    )
    world.say(f"First, {hero.label} {scenario.first_try}. Then {scenario.clue}.")
    world.say(SCENARIO_LINES[(params.seed or 0) % len(SCENARIO_LINES)].format(hero=hero.label, helper=helper.label))
    world.say(
        f"They chose {scenario.coax_method}. {helper.label} {scenario.helper_action}, "
        f"while {hero.label} waited behind the safety fence."
    )
    world.say(f"At last, {scenario.discovery}.")
    world.say(f"Together they {scenario.resolution}.")
    world.say(f"{hero.label} learned that {scenario.lesson}.")
    world.say(scenario.ending)

    hero.meters["safety"] = 1.0
    helper.meters["helpfulness"] = 1.0
    pod.meters["safe"] = 1.0
    hero.memes["patience"] = 1.0
    helper.memes["coaxing"] = 1.0

    world.facts = {
        "scenario": scenario,
        "hero": hero,
        "helper": helper,
        "pod": pod,
        "conflict": scenario.conflict,
        "first_try": scenario.first_try,
        "clue": scenario.clue,
        "coax_method": scenario.coax_method,
        "discovery": scenario.discovery,
        "resolution": scenario.resolution,
        "lesson": scenario.lesson,
        "ending": scenario.ending,
        "resolved": True,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    scenario: Scenario = world.facts["scenario"]
    return [
        f"Write a fable about {hero.label} and {helper.label} coaxing a pod to safety at a construction site.",
        f"Tell a child-friendly conflict story in which patience resolves this problem: {scenario.conflict}.",
        f"Write a construction-site fable showing why gentle coaxing is better than forcing a solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    return [
        QAItem(
            "Where did the story happen, and how did the friends stay safe?",
            f"It happened at the construction site. {hero.label} and {helper.label} stayed behind the striped safety fence and used help from the workers.",
        ),
        QAItem(
            f"What conflict did {hero.label} and {helper.label} face?",
            f"They faced this conflict: {world.facts['conflict']}.",
        ),
        QAItem(
            f"What did {hero.label} try first, and what clue changed the plan?",
            f"First, {hero.label} {world.facts['first_try']}. The clue was that {world.facts['clue']}.",
        ),
        QAItem(
            "How did coaxing help?",
            f"They used {world.facts['coax_method']}. This let them discover that {world.facts['discovery']}.",
        ),
        QAItem(
            "How did the story end, and what was the lesson?",
            f"Together they {world.facts['resolution']} {hero.label} learned that {world.facts['lesson']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is coaxing?", "Coaxing is encouraging something gently instead of forcing it."),
        QAItem("What is a pod?", "A pod is a small case that can protect seeds or other growing parts of a plant."),
        QAItem("Why is a construction site dangerous?", "A construction site has heavy tools, vehicles, and unfinished surfaces, so children must stay with adults in marked safe areas."),
        QAItem("What can end a conflict?", "Listening, speaking calmly, and finding a safe plan together can help end a conflict."),
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: type={entity.type} label={entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"facts: resolved={world.facts.get('resolved')} conflict={world.facts.get('conflict')}")
    return "\n".join(lines)


def asp_facts() -> str:
    return "\n".join(
        [
            "item(pod).",
            "at(pod,construction_site).",
            "conflict(pod).",
            "curious(hero).",
            "helper(helper).",
            "coaxing(hero).",
            "safe_method(coaxing).",
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    try:
        from asp import atoms, one_model
    except ImportError:
        return True
    model = one_model(asp_program("#show resolved/1.\n#show happy_end/0."))
    return bool(atoms(model, "resolved")) and bool(atoms(model, "happy_end"))


def asp_verify() -> int:
    if not asp_valid():
        print("Mismatch between ASP and Python gate.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("resolved"):
            print("Generated story failed the Python resolution gate.")
            return 1
    print("OK: ASP and Python agree; generated stories resolve the construction-site conflict.")
    return 0


CURATED = [
    StoryParams("Luna", "girl", "Sage", "boy", "pod", 0),
    StoryParams("Milo", "boy", "Wren", "girl", "pod", 1),
    StoryParams("Nell", "girl", "Finn", "boy", "pod", 2),
    StoryParams("Ivy", "girl", "Theo", "boy", "pod", 3),
]


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/1.\n#show happy_end/0."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            from asp import atoms, one_model
            model = one_model(asp_program("#show resolved/1.\n#show happy_end/0."))
            print("ASP model:")
            print(f"  resolved={bool(atoms(model, 'resolved'))}")
            print(f"  happy_end={bool(atoms(model, 'happy_end'))}")
        except ImportError:
            print("ASP facts and rules are ready, but clingo is not installed.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        target = max(1, args.n)
        while len(samples) < target and index < max(50, target * 50):
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
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
        header = ""
        if args.all:
            header = f"### {sample.params.hero_name} and {sample.params.helper_name} at the construction site"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
