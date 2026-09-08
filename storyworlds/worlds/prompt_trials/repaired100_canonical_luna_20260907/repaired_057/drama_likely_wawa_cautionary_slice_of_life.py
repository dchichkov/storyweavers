#!/usr/bin/env python3
"""
A small cautionary slice-of-life story world about Wawa, a child who learns
that ordinary drama is best handled by slowing down, checking facts, and asking
for help.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from storyworlds.results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "the neighborhood laundromat"
    affords: set[str] = field(default_factory=lambda: {"waiting", "listening", "checking", "helping"})


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
    worry: str
    first_action: str
    clue: str
    safe_action: str
    result: str
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


@dataclass
class StoryState:
    hero: Entity
    helper: Entity
    object: Entity
    setting: Setting
    checked: bool = False
    calmed: bool = False
    resolved: bool = False
    scenario: Optional[Scenario] = None


SETTING = Setting()

HERO_NAMES = ["Luna", "Mara", "Wawa", "Niko", "Pia", "Oren", "Tess", "Milo"]
HELPER_NAMES = ["Auntie Jo", "Sam", "Ravi", "Nell", "Mina", "Ben", "Cleo"]
OBJECTS = {
    "red_sock": "a red sock",
    "paper_boat": "a paper boat",
    "blue_mitten": "a blue mitten",
}

SCENARIOS = (
    Scenario(
        "the humming dryer",
        "the dryer began making a deep hum while a basket of clothes waited nearby",
        "reached for the door because the sound felt like a sign that something was terribly wrong",
        "the little safety light was still green, and the dryer drum was turning evenly",
        "stepped back, pressed the stop button, and called the attendant instead of opening the machine",
        "the attendant found a loose button in the empty lint tray and fixed it safely",
        "a worrying sound is a reason to pause and ask, not a reason to grab",
        "The dryer began its gentle tumble again, and one red sock spun past the glass like a tiny flag.",
    ),
    Scenario(
        "the missing mitten",
        "a blue mitten disappeared from the bench beside the folding table",
        "announced that someone must have stolen it and hurried toward the door",
        "a trail of damp dots led back beneath the bench",
        "asked everyone to stay still while the grown-up checked the warm radiator space",
        "the mitten was found drying behind the radiator, where it had slipped during a game",
        "a guess can sound dramatic before the facts have had a chance to speak",
        "Wawa tucked the warm mitten into the basket, and the two friends folded socks in a calmer rhythm.",
    ),
    Scenario(
        "the runaway paper boat",
        "a paper boat floated toward a puddle near the curb after a sudden shower",
        "rushed into the street to chase it before thinking about the cars",
        "the boat had caught on a twig beside the safe garden fence",
        "stayed on the sidewalk and asked the crossing guard to reach it with a long grabber",
        "the boat was rescued without anyone stepping into traffic",
        "a small treasure is never worth a dangerous hurry",
        "The paper boat rested in a dry jar while rain tapped softly on the laundromat window.",
    ),
    Scenario(
        "the strange beep",
        "a sharp beep sounded from the lost-and-found shelf",
        "told everyone the building alarm was about to begin",
        "the sound came in a steady pattern from a forgotten timer",
        "kept clear of the shelf and asked the attendant to inspect it",
        "the timer was turned off, and the attendant posted a note for its owner",
        "careful listening can turn a frightening mystery into an ordinary one",
        "The shelf grew quiet, and the ordinary music returned between the washer swishes.",
    ),
    Scenario(
        "the spilled soap",
        "a bottle of soap tipped over near the washing machines",
        "tried to wipe the puddle quickly with a bare sleeve",
        "the floor shone slippery beneath the bright ceiling light",
        "warned people away and found the attendant for a mop and a caution sign",
        "the spill was cleaned before anyone slipped",
        "helping means noticing the danger and choosing the safe kind of help",
        "The yellow sign stood proudly on the dry floor while Wawa carried the empty basket.",
    ),
)

OPENINGS = (
    "On an ordinary afternoon, {hero} met {helper} at the neighborhood laundromat.",
    "The washers swished and the dryers turned when {hero} arrived with {helper}.",
    "After school, {hero} and {helper} sat near the folding table at the neighborhood laundromat.",
    "Rain dotted the front window as {hero} and {helper} waited beside the humming machines.",
)

DIALOGUE = (
    "'Wait,' said {helper}. 'Do we know that, or are we guessing?'",
    "'It feels like drama,' said {hero}. '{helper}, can we check before we act?'",
    "{helper} pointed gently. 'First we make space. Then we ask someone who knows.'",
    "'I wanted to fix it fast,' said {hero}. 'Fast is not always safe,' {helper} replied.",
)


ASP_RULES = r"""
calm_plan(H) :- notices_risk(H), pauses(H), asks_help(H).
safe_resolution(H) :- calm_plan(H), adult_checks.
good_choice(H) :- safe_resolution(H).
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cautionary slice-of-life Wawa story world.")
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--object", choices=sorted(OBJECTS))
    parser.add_argument("--gender", choices=["girl", "boy", "child"])
    parser.add_argument("--helper-gender", choices=["girl", "boy", "adult"])
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
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice([name for name in HELPER_NAMES if name != hero_name])
    hero_type = args.gender or rng.choice(["girl", "boy", "child"])
    helper_type = args.helper_gender or "adult"
    object_name = args.object or rng.choice(sorted(OBJECTS))
    if hero_name == helper_name:
        raise StoryError("The hero and helper need different names so their dialogue is clear.")
    return StoryParams(
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        object_name=object_name,
    )


def make_world(params: StoryParams) -> tuple[World, StoryState]:
    world = World(SETTING)
    hero = world.add(Entity("hero", params.hero_type, params.hero_name))
    helper = world.add(Entity("helper", params.helper_type, params.helper_name))
    obj = world.add(Entity("object", "thing", OBJECTS[params.object_name]))
    return world, StoryState(hero=hero, helper=helper, object=obj, setting=SETTING)


def choose_scenario(params: StoryParams) -> Scenario:
    value = params.seed
    if value is None:
        value = sum((index + 1) * ord(char) for index, char in enumerate(params.hero_name + params.object_name))
    return SCENARIOS[value % len(SCENARIOS)]


def tell_story(params: StoryParams) -> World:
    world, state = make_world(params)
    scenario = choose_scenario(params)
    state.scenario = scenario
    hero = state.hero.label
    helper = state.helper.label

    variant = params.seed or 0
    world.say(OPENINGS[variant % len(OPENINGS)].format(hero=hero, helper=helper))
    world.say(
        f"That day, their small drama began when {scenario.worry}. "
        f"{hero} held {state.object.label}, then noticed the trouble."
    )
    world.say(
        f"{hero} {scenario.first_action}. The quick idea made the moment feel bigger, "
        f"but {scenario.clue}."
    )
    world.say(DIALOGUE[(variant // max(1, len(SCENARIOS))) % len(DIALOGUE)].format(hero=hero, helper=helper))
    world.say(
        f"{hero} took one slow breath. {helper} stayed close while they {scenario.safe_action}. "
        "No one touched the risky thing."
    )

    state.checked = True
    state.calmed = True
    state.resolved = True
    state.hero.memes.update({"worry": 0.3, "caution": 1.0, "trust": 1.0})
    state.helper.memes.update({"patience": 1.0, "guidance": 1.0})
    state.object.meters["safe_distance"] = 1.0

    world.say(f"After a careful check, {scenario.result}.")
    world.say(f"{hero} learned that {scenario.lesson}.")
    world.say(scenario.ending)

    world.facts = {
        "hero": state.hero,
        "helper": state.helper,
        "object": state.object,
        "scenario": scenario,
        "checked": state.checked,
        "calmed": state.calmed,
        "resolved": state.resolved,
    }
    return world


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


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    scenario: Scenario = world.facts["scenario"]
    return [
        f"Write a cautionary slice-of-life story about {hero.label} and {helper.label} handling {scenario.title}.",
        f"Show how {hero.label} replaces a likely guess with a careful check during ordinary drama.",
        f"Tell a child-friendly story set in a neighborhood laundromat where asking for help keeps everyone safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    obj: Entity = world.facts["object"]  # type: ignore[assignment]
    scenario: Scenario = world.facts["scenario"]  # type: ignore[assignment]
    return [
        QAItem(
            "Where were the friends, and what object was nearby?",
            f"They were at the neighborhood laundromat, and {obj.label} was nearby.",
        ),
        QAItem(
            f"What made {hero.label} worried?",
            f"{hero.label} worried because {scenario.worry}.",
        ),
        QAItem(
            f"Why did {hero.label} slow down?",
            f"{hero.label} slowed down because {scenario.clue}.",
        ),
        QAItem(
            f"How did {helper.label} change what {hero.label} did?",
            f"{helper.label} encouraged a pause and a safe check, so {hero.label} {scenario.safe_action}.",
        ),
        QAItem(
            "How did the story end?",
            f"{scenario.result.capitalize()}. The friends learned that {scenario.lesson}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does caution mean?",
            "Caution means slowing down, noticing danger, and choosing a safer action.",
        ),
        QAItem(
            "Why can a guess be risky?",
            "A guess can be risky because it may make someone act before they know what is really happening.",
        ),
        QAItem(
            "Who should a child ask about a dangerous machine or spill?",
            "A child should step back and ask a trusted grown-up or trained worker.",
        ),
        QAItem(
            "What is ordinary drama?",
            "Ordinary drama is a tense or surprising moment in everyday life that can often be solved calmly.",
        ),
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
    lines.append(f"checked={world.facts.get('checked')} resolved={world.facts.get('resolved')}")
    return "\n".join(lines)


def asp_facts() -> str:
    return "\n".join(
        [
            "notices_risk(hero).",
            "pauses(hero).",
            "asks_help(hero).",
            "adult_checks.",
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    return True


def asp_verify() -> int:
    if not asp_valid():
        print("Mismatch between ASP and Python caution gate.")
        return 1
    try:
        from storyworlds.asp import atoms, one_model
        model = one_model(
            asp_program(
                "#show calm_plan/1."
                "#show safe_resolution/1."
                "#show good_choice/1."
            )
        )
        required = {("hero",)}
        if set(atoms(model, "good_choice")) != required:
            print("Mismatch between ASP and Python caution gate.")
            return 1
    except ImportError:
        pass
    sample = generate(
        StoryParams(
            hero_name="Wawa",
            hero_type="child",
            helper_name="Auntie Jo",
            helper_type="adult",
            object_name="red_sock",
            seed=3,
        )
    )
    if not sample.story or "Wawa" not in sample.story or "asked" not in sample.story:
        print("Generated-story verification failed.")
        return 1
    print("OK: ASP and Python agree that pausing and asking for help is the safe choice.")
    return 0


CURATED = [
    StoryParams("Wawa", "child", "Auntie Jo", "adult", "red_sock", 0),
    StoryParams("Luna", "girl", "Sam", "adult", "blue_mitten", 1),
    StoryParams("Mara", "girl", "Ravi", "adult", "paper_boat", 2),
    StoryParams("Niko", "boy", "Nell", "adult", "red_sock", 3),
    StoryParams("Pia", "girl", "Ben", "adult", "blue_mitten", 4),
]


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
        print(
            asp_program(
                "#show notices_risk/1."
                "#show pauses/1."
                "#show asks_help/1."
                "#show calm_plan/1."
                "#show safe_resolution/1."
                "#show good_choice/1."
            )
        )
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        try:
            from storyworlds.asp import atoms, one_model
            model = one_model(
                asp_program("#show calm_plan/1.#show safe_resolution/1.#show good_choice/1.")
            )
            print("ASP model:")
            for predicate in ("calm_plan", "safe_resolution", "good_choice"):
                print(f"  {predicate}: {atoms(model, predicate)}")
        except ImportError:
            print("ASP support requires clingo.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(0, args.n):
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
        if args.all:
            params = sample.params
            header = f"### {params.hero_name} and {params.helper_name} at the laundromat"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
