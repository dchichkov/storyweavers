#!/usr/bin/env python3
"""
A heartwarming wilderness story world about a gentle hulk, a hidden warning,
and friends who solve a forest problem together.
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
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Scenario:
    warning: str
    danger: str
    clue: str
    task: str
    result: str
    ending: str
    warning_answer: str
    teamwork_answer: str


@dataclass
class StoryParams:
    name: str
    companion: str
    kindness: str
    seed: Optional[int] = None


NAMES = ["Luna", "Mara", "Niko", "Tala", "Suri", "Ari"]
COMPANIONS = ["a small fox", "a bright blue jay", "a shy deer", "a patient tortoise"]
KINDNESSES = ["gentle", "thoughtful", "brave", "patient"]

SCENARIOS = [
    Scenario(
        warning="the old pine dropped three cones in a row",
        danger="a storm-bent tree was ready to fall across the trail",
        clue="fresh scratches on the moss pointed toward a safer meadow path",
        task="Luna held up a red ribbon while the hulk moved the loose branches one by one",
        result="The hulk cleared the trail without touching the leaning tree, and everyone reached the meadow safely",
        ending="The rescued birds sang from the meadow while the hulk sat beneath the steady pines, smiling softly",
        warning_answer="The old pine dropped three cones in a row as a warning.",
        teamwork_answer="Luna noticed the warning and guided the hulk, while the hulk carefully moved branches away from the dangerous tree.",
    ),
    Scenario(
        warning="the creek water suddenly carried a ring of yellow leaves",
        danger="a hidden bank had begun to crumble near the usual crossing",
        clue="smooth stones made a high crossing beside a patch of silver ferns",
        task="the companion marked the stones while the hulk carried fallen logs away from the crumbling bank",
        result="They crossed above the weak bank, leaving the creek clear for the animals",
        ending="Sunlight shone on the silver ferns, and the hulk shared warm berries with every tired traveler",
        warning_answer="A ring of yellow leaves in the creek warned them that the bank was crumbling.",
        teamwork_answer="The companion marked the safe stones while the hulk cleared logs away from the weak bank.",
    ),
    Scenario(
        warning="a family of rabbits froze beside the path",
        danger="a rockslide was rumbling behind the blackberry bushes",
        clue="rabbit tracks led toward a quiet hollow under a wide cedar",
        task="the hulk gently lifted a fallen log while Luna helped the rabbits follow the tracks",
        result="The rabbits reached the cedar hollow before the loose rocks rolled onto the empty path",
        ending="The rabbits peeked from their safe hollow as the hulk made a tiny shelter sign from twigs",
        warning_answer="The frozen rabbits warned them that rocks were rumbling nearby.",
        teamwork_answer="The hulk lifted the fallen log gently while Luna guided the rabbits toward the cedar hollow.",
    ),
    Scenario(
        warning="the fireflies blinked all at once and then went dark",
        danger="a smoky patch of wilderness hid a small grass fire beyond the ridge",
        clue="a damp trail beside the brook led around the smoke",
        task="Luna soaked a cloth while the hulk pressed a wide leaf over the smallest flames",
        result="They reached the ranger's water barrel by the damp trail and helped stop the little fire",
        ending="The fireflies returned at dusk, blinking like tiny stars around the thankful hulk",
        warning_answer="The fireflies going dark warned them about smoke and a small grass fire.",
        teamwork_answer="Luna prepared a wet cloth while the hulk covered the smallest flames, and together they reached water.",
    ),
]

OPENINGS = [
    "In the deep wilderness, {name} lived beside a mossy trail with {companion}.",
    "At the edge of the wilderness, {name} met a huge green hulk who was gentle enough to carry a sleeping moth without waking it.",
    "One bright morning in the wilderness, {name} and {companion} found the hulk gathering berries for hungry birds.",
    "The wilderness was full of tall trees, soft moss, and one very large hulk with a very careful heart.",
]

MORALS = [
    "A warning is a gift when someone cares enough to notice it.",
    "Being strong is most wonderful when strength is used gently.",
    "Good friends listen to small clues before a big problem arrives.",
    "A careful heart can make a great hulk feel safe enough to help.",
]


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.events: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.events.append(text)

    def render(self) -> str:
        return "\n\n".join(self.events)


SETTING = Setting(
    place="the deep wilderness",
    affords={"forest", "warning", "help", "safety"},
)

def valid_combos() -> list[tuple[str, str, str]]:
    return [(name, companion, kindness) for name in NAMES for companion in COMPANIONS for kindness in KINDNESSES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    companion = args.companion or rng.choice(COMPANIONS)
    kindness = args.kindness or rng.choice(KINDNESSES)
    if name not in NAMES:
        raise StoryError(f"unknown name: {name}")
    if companion not in COMPANIONS:
        raise StoryError(f"unknown companion: {companion}")
    if kindness not in KINDNESSES:
        raise StoryError(f"unknown kindness: {kindness}")
    return StoryParams(name=name, companion=companion, kindness=kindness)


def tell(params: StoryParams) -> World:
    seed = params.seed if params.seed is not None else sum((i + 1) * ord(c) for i, c in enumerate(params.name + params.companion + params.kindness))
    rng = random.Random(seed)
    scenario = rng.choice(SCENARIOS)
    world = World(SETTING)

    hero = world.add(Entity(params.name, "character", params.name, "child"))
    companion = world.add(Entity("companion", "animal", params.companion, "animal"))
    hulk = world.add(Entity("hulk", "character", "the hulk", "hulk"))
    hero.memes["care"] = 1
    hulk.meters["strength"] = 3
    hulk.memes["gentleness"] = 2
    world.facts.update(hero=hero, companion=companion, hulk=hulk, scenario=scenario)

    companion_cap = params.companion[0].upper() + params.companion[1:]
    world.say(OPENINGS[rng.randrange(len(OPENINGS))].format(
        name=params.name,
        companion=params.companion,
    ))
    world.say(
        f"The hulk looked frightening at first, but {params.name} knew the hulk was "
        f"{params.kindness} and loved helping small creatures."
    )
    world.say(
        f"That morning they carried berries toward a nest near the trail. "
        f"{companion_cap} trotted beside them, listening to every sound."
    )
    world.say(
        f"Then {scenario.warning}. {params.name} stopped and whispered, "
        f'"Something is telling us to wait."'
    )
    world.say(
        f'"Should I keep going?" asked the hulk. '
        f'"Not yet," said {params.name}. "Let us find out what the wilderness is saying."'
    )
    hero.meters["uncertainty"] = 1
    hero.memes["attention"] = 1
    hulk.memes["trust"] = 1

    world.say(f"They soon discovered that {scenario.danger}.")
    world.say(
        f"The hulk clenched both huge hands. \"I can fix it quickly,\" the hulk said."
    )
    world.say(
        f'"Quickly is not always safely," {params.name} replied. '
        f'"We can use your strength carefully, and our eyes together."'
    )
    world.say(f"{scenario.clue.capitalize()}.")
    world.say(
        f"{companion_cap} chirped, " + '"The safe way is over there!"'
    )
    hero.memes["confidence"] = 1
    hulk.memes["patience"] = 1

    world.say(f"{scenario.task.capitalize()}.")
    world.say(f"{scenario.result}.")
    hero.meters["uncertainty"] = 0
    hulk.meters["danger"] = 0
    hulk.memes["joy"] = 1
    hero.memes["joy"] = 1

    world.say(
        f"At last, the nest was safe and the berries were delivered. "
        f"The hulk lowered the hulk's shoulders, and {params.name} gave the hulk a warm hug."
    )
    world.say(f'"You were strong enough to listen," {params.name} said.')
    world.say(f'"And you were brave enough to notice," said the hulk.')
    world.say(f"{scenario.ending}.")
    world.say(f"They remembered this lesson: {rng.choice(MORALS)}")
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            "Write a heartwarming wilderness story about a gentle hulk who listens to a warning.",
            f"Tell a child-friendly tale about {params.name}, {params.companion}, and a hulk solving a wilderness problem.",
            "Include foreshadowing, conflict, teamwork, and a warm ending.",
        ],
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    scenario = world.facts["scenario"]
    return [
        QAItem("Who traveled through the wilderness?", f"{hero.label}, {world.facts['companion'].label}, and the gentle hulk traveled together."),
        QAItem("What warning did they notice?", scenario.warning_answer),
        QAItem("What danger did the warning reveal?", f"The warning revealed that {scenario.danger}."),
        QAItem("How did the friends solve the conflict?", scenario.teamwork_answer),
        QAItem("What changed in the hulk?", "The hulk learned to use great strength patiently and gently instead of rushing."),
        QAItem("What lesson did they learn?", "They learned that careful listening and teamwork can turn a frightening problem into a safe ending."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is wilderness?", "Wilderness is a natural place with plants, animals, and little human building."),
        QAItem("What is a hulk?", "A hulk is a very large and powerful person or creature."),
        QAItem("What is foreshadowing?", "Foreshadowing is a small clue that hints something important may happen later."),
        QAItem("Why should strong people be gentle?", "Gentleness helps strength protect others instead of hurting them."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(f"{entity.id}: meters={entity.meters} memes={entity.memes}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "wilderness"), asp.fact("theme", "hulk")]
    for name in NAMES:
        lines.append(asp.fact("name", name.lower()))
    for kindness in KINDNESSES:
        lines.append(asp.fact("kindness", kindness))
    lines.append(asp.fact("has_warning", "wilderness"))
    lines.append(asp.fact("has_conflict", "wilderness"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(N, K) :- name(N), kindness(K), has_warning(wilderness), has_conflict(wilderness).
#show valid_story/2.
"""


def asp_program(show: str = "#show valid_story/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = {(name.lower(), kindness) for name in NAMES for kindness in KINDNESSES}
    actual = set(asp_valid_combos())
    if expected == actual:
        print(f"OK: ASP and Python agree ({len(actual)} combinations).")
        return 0
    print("ASP/Python mismatch.")
    print("Only Python:", sorted(expected - actual))
    print("Only ASP:", sorted(actual - expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A heartwarming wilderness hulk story world.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--kindness", choices=KINDNESSES)
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams("Luna", "a small fox", "gentle", base_seed),
            StoryParams("Mara", "a bright blue jay", "thoughtful", base_seed + 1),
            StoryParams("Niko", "a shy deer", "brave", base_seed + 2),
            StoryParams("Tala", "a patient tortoise", "patient", base_seed + 3),
        ]
    else:
        params_list = []
        for index in range(args.n):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            params_list.append(params)

    samples = [generate(params) for params in params_list]
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
