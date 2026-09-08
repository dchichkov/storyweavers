#!/usr/bin/env python3
"""
A tiny mythic storyworld about a spy whose careful courage brings a happy ending.
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
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    id: str
    label: str
    feature: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Mission:
    id: str
    title: str
    omen: str
    danger: str
    clue: str
    secret: str
    helper_reason: str
    choice: str
    action: str
    happy_result: str
    ending_image: str
    lesson: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    history: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, sentence: str) -> None:
        self.history.append(sentence)

    def render(self) -> str:
        return "\n\n".join(self.history)


SETTINGS = {
    "moon_garden": Setting(
        "moon_garden",
        "the Moon Garden",
        "a silver garden beneath a quiet moon",
        {"light": 1.0, "safety": 0.0},
        {"wonder": 1.0},
    ),
    "cloud_bridge": Setting(
        "cloud_bridge",
        "the Cloud Bridge",
        "a bright bridge above the sleeping valleys",
        {"height": 1.0, "safety": 0.0},
        {"wonder": 1.0},
    ),
    "whispering_forest": Setting(
        "whispering_forest",
        "the Whispering Forest",
        "an old forest where leaves remembered every promise",
        {"shadow": 1.0, "safety": 0.0},
        {"wonder": 1.0},
    ),
}

MISSIONS = {
    "star_lantern": Mission(
        "star_lantern",
        "The Lantern of Returning Light",
        "the stars had begun to fade before dawn",
        "a jealous shadow guarded the last star-lantern",
        "three blue feathers beside a dry stream",
        "the lantern was not stolen; it was hiding from a lonely shadow",
        "the shadow had once guided travelers, but everyone had forgotten to thank it",
        "to speak with the shadow instead of tricking it",
        "listened until the shadow shared the lantern's flame",
        "the stars shone again, and the shadow became a gentle guide",
        "the moon placed a small silver crown on the spy's head",
        "even a hidden heart may be waiting for kindness",
    ),
    "golden_thread": Mission(
        "golden_thread",
        "The Thread of Togetherness",
        "the roads of the kingdom had begun to untie themselves",
        "a giant moth had wrapped the golden road-thread around a lonely tower",
        "tiny footprints crossing a bridge of fallen petals",
        "the moth was protecting a nest woven from the kingdom's old songs",
        "the nest would fall if the thread were pulled too quickly",
        "to ask the moth for a safer way to mend the roads",
        "wove a new nest cord while the moth returned the golden thread",
        "the roads joined once more, and travelers found one another safely",
        "the tower bells rang for every creature who had helped",
        "careful listening can turn a tangle into a path",
    ),
    "rainbow_key": Mission(
        "rainbow_key",
        "The Key Beneath the Rainbow",
        "the gate to spring had forgotten how to open",
        "a proud river kept the rainbow key under its rushing water",
        "a line of bright stones leading away from the riverbank",
        "the river was holding the key because no one had heard its tired song",
        "the river needed a quiet listener, not a stronger hand",
        "to sit beside the water and let the river tell its story",
        "answered the river with a song and received the key",
        "the gate opened, and spring poured flowers across the land",
        "rainbow drops danced around the spy's boots",
        "patience can unlock what force only hides",
    ),
    "sleeping_bell": Mission(
        "sleeping_bell",
        "The Bell That Remembered",
        "the village bell had slept through every morning",
        "a dragon curled around the bell in the hill",
        "warm ash arranged in a circle like a nest",
        "the dragon was guarding an egg beneath the bell",
        "the bell's loud ringing frightened the unborn dragon",
        "to make a soft promise before touching the bell",
        "laid a gentle rhythm on the bell while the dragon carried its egg away",
        "the bell woke softly and welcomed the new dragon",
        "the village children heard music instead of thunder",
        "a gentle promise can make room for a new beginning",
    ),
}

NAMES = ["Luna", "Mira", "Orin", "Nia", "Tavi", "Sola"]
HELPERS = ["the moon fox", "the river giant", "the little dragon", "the star owl", "the old tree"]

GENDERS = {
    "Luna": "girl",
    "Mira": "girl",
    "Nia": "girl",
    "Sola": "girl",
    "Orin": "boy",
    "Tavi": "boy",
}


@dataclass
class StoryParams:
    setting: str
    mission: str
    name: str
    helper: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(setting, mission) for setting in SETTINGS for mission in MISSIONS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None)
    mission = getattr(args, "mission", None)
    if setting is not None and setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {setting}")
    if mission is not None and mission not in MISSIONS:
        raise StoryError(f"Unknown mission: {mission}")
    choices = [
        pair for pair in valid_combos()
        if (setting is None or pair[0] == setting)
        and (mission is None or pair[1] == mission)
    ]
    if not choices:
        raise StoryError("No compatible setting and mission were found.")
    chosen_setting, chosen_mission = rng.choice(choices)
    return StoryParams(
        setting=chosen_setting,
        mission=chosen_mission,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        helper=getattr(args, "helper", None) or rng.choice(HELPERS),
    )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)
    spy = world.add(
        Entity(
            "spy",
            "character",
            params.name,
            memes={"courage": 1.0, "curiosity": 1.0, "trust": 0.0},
        )
    )
    helper = world.add(Entity("helper", "helper", params.helper, memes={"wisdom": 1.0}))
    world.facts.update(
        {
            "spy": spy,
            "helper": helper,
            "mission": MISSIONS[params.mission],
            "happy_ending": False,
        }
    )
    return world


def _rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed ^ 0xA31F29)
    text = "|".join((params.setting, params.mission, params.name, params.helper))
    return random.Random(sum((i + 1) * ord(ch) for i, ch in enumerate(text)))


def _opening(rng: random.Random, world: World, spy: Entity, mission: Mission) -> str:
    openings = [
        f"Long ago, beneath {world.setting.feature}, lived {spy.label}, a young spy with quiet eyes and a brave heart.",
        f"In the first age of moonlight, {spy.label} served as a spy in {world.setting.label}, where even stones remembered old songs.",
        f"One bright night, when {world.setting.feature} glittered like a promise, {spy.label} received a secret mission.",
    ]
    return rng.choice(openings)


def _discovery(rng: random.Random, spy: Entity, mission: Mission) -> list[str]:
    return [
        f"The message said, \"{mission.omen}.\"",
        f"{spy.label} followed a trail of signs and found {mission.clue}.",
        f"At the end of the trail waited danger: {mission.danger}.",
    ]


def _dialogue(rng: random.Random, spy: Entity, helper: Entity, mission: Mission) -> list[str]:
    first = rng.choice(
        [
            f"\"I must pass,\" said {spy.label}. \"The kingdom needs me.\"",
            f"\"Tell me the secret,\" {spy.label} whispered. \"I do not want to make a mistake.\"",
            f"{spy.label} raised a hand and said, \"I came to help, not to harm.\"",
        ]
    )
    answer = rng.choice(
        [
            f"\"Then listen before you act,\" answered {helper.label}. \"{mission.helper_reason.capitalize()}.\"",
            f"{helper.label} replied, \"A true spy notices more than danger. {mission.helper_reason.capitalize()}.\"",
            f"\"Your courage is good,\" said {helper.label}, \"but {mission.helper_reason}.\"",
        ]
    )
    return [first, answer]


def _resolution(rng: random.Random, spy: Entity, mission: Mission) -> list[str]:
    return [
        f"{spy.label} chose {mission.choice}.",
        f"With patient courage, {spy.label} {mission.action}.",
        f"Then {mission.happy_result}.",
        f"{mission.ending_image.capitalize()}. The mission ended in a happy ending, and {spy.label} returned home beneath the kindly stars.",
    ]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.mission not in MISSIONS:
        raise StoryError(f"Unknown mission: {params.mission}")
    world = build_world(params)
    spy = world.entities["spy"]
    helper = world.entities["helper"]
    mission = MISSIONS[params.mission]
    rng = _rng(params)

    world.facts["omen"] = mission.omen
    world.facts["danger"] = mission.danger
    world.facts["secret"] = mission.secret
    world.setting.memes["wonder"] = 1.0
    world.say(_opening(rng, world, spy, mission))
    world.say("The spy carried no sword, only a small blue cloak, a listening ear, and a promise to protect the people.")
    world.say("The mission began when the oldest moon announced that the kingdom needed help.")
    world.say(" ".join(_discovery(rng, spy, mission)))
    world.say(" ".join(_dialogue(rng, spy, helper, mission)))
    world.say("The secret became clear: " + mission.secret + ".")
    world.say(" ".join(_resolution(rng, spy, mission)))

    spy.memes["trust"] = 1.0
    spy.memes["relief"] = 1.0
    world.setting.meters["safety"] = 1.0
    world.facts["happy_ending"] = True
    world.facts["lesson"] = mission.lesson

    story = world.render()
    prompts = [
        "Write a short myth about a spy who chooses kindness and reaches a happy ending.",
        f"Tell a mythic spy story set in {world.setting.label}.",
        f"Write a gentle adventure where {params.name} listens before acting.",
    ]
    story_qa = [
        QAItem(
            "Who was the spy?",
            f"{params.name} was the brave spy who carried out the mission.",
        ),
        QAItem(
            "Where did the mission happen?",
            f"The mission happened in {world.setting.label}, {world.setting.feature}.",
        ),
        QAItem(
            "What danger did the spy discover?",
            f"The spy discovered that {mission.danger}.",
        ),
        QAItem(
            "What secret changed the spy's plan?",
            f"The secret was that {mission.secret}.",
        ),
        QAItem(
            "How did the story end?",
            f"{mission.happy_result.capitalize()}, and {params.name} returned home beneath the kindly stars.",
        ),
    ]
    world_qa = [
        QAItem(
            "What is a spy?",
            "A spy is a careful observer who learns important information and uses it responsibly.",
        ),
        QAItem(
            "What makes a myth?",
            "A myth is an imaginative old-style tale with wonder, memorable figures, and a lesson.",
        ),
        QAItem(
            "What is a happy ending?",
            "A happy ending is a conclusion in which the main problem is safely resolved and hope remains.",
        ),
        QAItem(
            "What lesson did the spy learn?",
            f"The spy learned that {mission.lesson}.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(
        f"setting={world.setting.id} meters={world.setting.meters} memes={world.setting.memes}"
    )
    for entity in world.entities.values():
        lines.append(
            f"{entity.id} ({entity.kind}) meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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


ASP_RULES = r"""
valid(Setting, Mission) :- setting(Setting), mission(Mission).
safe(Setting, Mission) :- valid(Setting, Mission), happy_ending(Mission).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for setting in SETTINGS:
        lines.append(asp.fact("setting", setting))
    for mission in MISSIONS:
        lines.append(asp.fact("mission", mission))
        lines.append(asp.fact("happy_ending", mission))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set != asp_set:
        print("ASP/Python parity mismatch.")
        print("Only in Python:", sorted(python_set - asp_set))
        print("Only in ASP:", sorted(asp_set - python_set))
        return 1
    for index, (setting, mission) in enumerate(sorted(python_set)[:5]):
        sample = generate(
            StoryParams(setting=setting, mission=mission, name="Luna", helper="the moon fox", seed=index)
        )
        if not sample.story or not sample.world.facts["happy_ending"]:
            print("Generated-story verification failed.")
            return 1
    print(f"OK: ASP matches Python ({len(python_set)} combinations), and stories resolve happily.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A mythic spy storyworld with a happy ending."
    )
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--mission", choices=MISSIONS)
    parser.add_argument("--name")
    parser.add_argument("--helper")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, (setting, mission) in enumerate(valid_combos()):
            samples.append(
                generate(
                    StoryParams(
                        setting=setting,
                        mission=mission,
                        name="Luna",
                        helper="the moon fox",
                        seed=base_seed + index,
                    )
                )
            )
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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
