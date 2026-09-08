#!/usr/bin/env python3
"""
A gentle detective storyworld about a blizzard, a missing biscuit, and
reconciliation on a forest trail.

A blizzard hides a trail marker and scatters a biscuit tin. Two young detectives
blame each other until they compare clues, discover the wind caused the trouble,
and reconcile by repairing the trail together.
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
    place: str
    affords: set[str]
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    object_label: str


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
    "forest_trail": Setting(
        id="forest_trail",
        place="the forest trail",
        affords={"trail_search", "shelter_check"},
        meters={"visibility": 0.3, "snow_depth": 1.0},
        memes={"uncertainty": 1.0},
    ),
}

TASKS = {
    "trail_search": Task(
        id="trail_search",
        verb="follow the forest trail",
        gerund="following the forest trail",
        object_label="the trail markers",
    ),
    "shelter_check": Task(
        id="shelter_check",
        verb="check the forest shelter",
        gerund="checking the forest shelter",
        object_label="the shelter door",
    ),
}

GIRL_NAMES = ["Luna", "Maya", "Ivy", "Nora"]
BOY_NAMES = ["Theo", "Finn", "Owen", "Eli"]

ARCS = [
    {
        "opening": "Luna carried a small biscuit tin while Theo carried a red notebook for clues.",
        "problem": "A blizzard rushed through the pines, and the tin vanished beside a crooked trail marker.",
        "clue": "They found biscuit crumbs leading toward the marker, but the wind had blown them in two directions.",
        "cause": "The blizzard had lifted the loose tin lid and rolled the tin beneath a low spruce branch.",
        "repair": "Luna tied the lid shut while Theo reset the marker in the snow.",
        "ending": "The biscuit tin sat safely in the middle of their shared map.",
    },
    {
        "opening": "Luna and Theo set out with warm biscuits to share at the forest shelter.",
        "problem": "A white wall of blizzard snow covered the trail, and one biscuit disappeared from the open pouch.",
        "clue": "A round mark in the snow looked like a boot print until Luna noticed a tiny crumb inside it.",
        "cause": "The biscuit had slipped through a tear in the pouch and landed beneath Theo's snowshoe.",
        "repair": "Theo emptied the pouch carefully while Luna mended the tear with a strip of cloth.",
        "ending": "They divided the rescued biscuits equally before walking on.",
    },
    {
        "opening": "Luna drew each trail sign while Theo packed a biscuit for their hungry return trip.",
        "problem": "The blizzard spun the paper signs away, and the biscuit was missing when they reached a fork.",
        "clue": "A blue thread on a thorn matched the thread around Luna's sign bundle.",
        "cause": "The wind had caught the bundle, and the biscuit had been tucked inside it by mistake.",
        "repair": "They gathered the signs together and placed the biscuit in a closed pocket.",
        "ending": "Their neat signs pointed home while the biscuit waited for teatime.",
    },
]

DIALOGUE = [
    '"You took the biscuit," said Theo. "I saw you near the tin." "I was looking for the marker," Luna replied. "Let us compare clues before we decide."',
    '"The trail is confusing," Luna said. "Are you sure I moved the tin?" Theo shook snow from his mitten. "No. I am sure only that it is gone. We should investigate together."',
    '"I felt blamed," said Theo. "I felt unheard," Luna answered. "Then we can fix both things by listening carefully now."',
]

@dataclass
class StoryParams:
    place: str
    task: str
    detective: str
    partner: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A blizzard biscuit reconciliation detective story.")
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--task", choices=TASKS)
    parser.add_argument("--detective")
    parser.add_argument("--partner")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "forest_trail"
    task = args.task or rng.choice(list(TASKS))
    detective = args.detective or rng.choice(GIRL_NAMES)
    choices = [name for name in GIRL_NAMES + BOY_NAMES if name != detective]
    partner = args.partner or rng.choice(choices)
    if detective == partner:
        raise StoryError("The two detectives must have different names.")
    return StoryParams(place, task, detective, partner, getattr(args, "seed", None))


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    task = TASKS[params.task]
    world = World(setting)
    detective = world.add(Entity(params.detective, "character", params.detective))
    partner = world.add(Entity(params.partner, "character", params.partner))
    biscuit = world.add(Entity("biscuit", "food", "the biscuit"))
    marker = world.add(Entity("marker", "object", "the trail marker"))
    tin = world.add(Entity("tin", "object", "the biscuit tin"))

    index = (params.seed or 0) % len(ARCS)
    arc = ARCS[index]
    dialogue = DIALOGUE[((params.seed or 0) // len(ARCS)) % len(DIALOGUE)]

    detective.memes.update({"trust": 0.4, "worry": 0.5})
    partner.memes.update({"trust": 0.4, "worry": 0.5})
    setting.meters["visibility"] = 0.2
    setting.meters["snow_depth"] = 1.0

    world.say(f"{detective.label} and {partner.label} were {task.gerund} on {setting.place}.")
    world.say(arc["opening"])
    world.say("They were young detectives, and their rule was to solve a mystery with clues instead of guesses.")

    world.para()
    world.say(arc["problem"])
    detective.memes["worry"] = 1.2
    partner.memes["worry"] = 1.2
    world.say(dialogue)

    world.para()
    world.say("They knelt together and examined the snow without arguing over what it meant.")
    world.say(arc["clue"])
    detective.memes["trust"] += 0.4
    partner.memes["trust"] += 0.4
    world.say(f"{detective.label} noticed a loose edge, while {partner.label} noticed that the wind had erased the older tracks.")

    world.para()
    world.say("The two clues fit together.")
    world.say(arc["cause"])
    world.say(f"{detective.label} looked at {partner.label}. \"I was too quick to blame you,\" said {detective.label}.")
    world.say(f"\"And I should have explained what I saw,\" said {partner.label}. \"Can we start again?\"")
    world.say(f"\"Yes,\" said {detective.label}. \"We can solve this together.\"")
    detective.memes["trust"] = 1.0
    partner.memes["trust"] = 1.0
    detective.memes["worry"] = 0.0
    partner.memes["worry"] = 0.0
    world.facts["reconciled"] = True

    world.para()
    world.say(arc["repair"])
    world.say("They shared the work, apologized clearly, and checked each other's steps.")
    world.say(arc["ending"])

    world.facts.update(
        detective=detective,
        partner=partner,
        biscuit=biscuit,
        marker=marker,
        tin=tin,
        arc=arc,
        task=task,
        resolution="They discovered that the blizzard moved the biscuit tin, then apologized and repaired the trail together.",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a gentle detective story about {f['detective'].label} and {f['partner'].label} investigating a missing biscuit on {world.setting.place}.",
        "Show a blizzard creating confusing clues, then let the detectives reconcile by listening and sharing the work.",
        f"Write a child-friendly mystery in which {f['resolution'].lower()}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            "Who investigated the mystery?",
            f"{f['detective'].label} and {f['partner'].label} investigated it together on {world.setting.place}.",
        ),
        QAItem(
            "What went missing during the blizzard?",
            "A biscuit tin carrying a biscuit went missing beside a crooked trail marker.",
        ),
        QAItem(
            "What caused the trouble?",
            f"{f['arc']['cause']}",
        ),
        QAItem(
            "How did the detectives reconcile?",
            f"They admitted that they had blamed and misunderstood each other, apologized, listened to the clues, and shared the repair work.",
        ),
        QAItem(
            "How did the story end?",
            f"{f['arc']['ending']} The detectives trusted each other again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a blizzard?", "A blizzard is a powerful snowstorm with strong wind and very poor visibility."),
        QAItem("What is a biscuit?", "A biscuit is a small baked food that can be eaten as a snack."),
        QAItem("What does reconcile mean?", "To reconcile means to make peace after a disagreement and restore a friendly relationship."),
        QAItem("What does a detective do?", "A detective studies clues and asks careful questions to understand what happened."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    for item in sample.story_qa + sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world ---", f"setting: {world.setting.place}"]
    lines.append(f"setting_meters: {world.setting.meters}")
    lines.append(f"setting_memes: {world.setting.memes}")
    for entity in world.entities.values():
        lines.append(f"{entity.id}: {entity.kind}, meters={entity.meters}, memes={entity.memes}")
    lines.append(f"facts: {world.facts.get('reconciled', False)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_place(P) :- setting(P).
valid_task(T) :- task(T).
valid_pair(P,T) :- affords(P,T).
clue_found :- valid_pair(forest_trail,trail_search).
reconciled :- clue_found, apology, shared_work.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for setting in SETTINGS.values():
        lines.append(asp.fact("setting", setting.id))
        for task in sorted(setting.affords):
            lines.append(asp.fact("affords", setting.id, task))
    for task in TASKS.values():
        lines.append(asp.fact("task", task.id))
    lines.append(asp.fact("apology"))
    lines.append(asp.fact("shared_work"))
    return "\n".join(lines)


def asp_program(show: str = "#show reconciled/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    python_valid = ("forest_trail", "trail_search") in {
        (place, task) for place, setting in SETTINGS.items() for task in setting.affords
    }
    if not python_valid:
        print("FAIL: Python does not permit the canonical forest trail task.")
        return 1
    try:
        import asp
        models = asp.solve(asp_program(), models=1)
        if not any(symbol.name == "reconciled" for symbol in models[0]):
            print("FAIL: ASP reconciliation parity check failed.")
            return 1
    except ImportError:
        pass
    for seed in range(6):
        params = StoryParams("forest_trail", "trail_search", "Luna", "Theo", seed)
        sample = generate(params)
        if "blizzard" not in sample.story or "biscuit" not in sample.story:
            print("FAIL: generated story lost required seed words.")
            return 1
        if "reconcile" not in sample.story.lower() and "apolog" not in sample.story.lower():
            print("FAIL: generated story lacks reconciliation.")
            return 1
    print("OK: Python/ASP parity and generated-story checks passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.place}")
    if params.task not in TASKS:
        raise StoryError(f"Unknown task: {params.task}")
    if params.detective == params.partner:
        raise StoryError("The detectives must have different names.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


CURATED = [
    StoryParams("forest_trail", "trail_search", "Luna", "Theo", 0),
    StoryParams("forest_trail", "shelter_check", "Maya", "Finn", 1),
    StoryParams("forest_trail", "trail_search", "Ivy", "Owen", 2),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for index in range(max(0, args.n)):
            rng = random.Random(base_seed + index)
            local_args = argparse.Namespace(**vars(args))
            local_args.seed = base_seed + index
            params = resolve_params(local_args, rng)
            samples.append(generate(params))

    if args.asp:
        print(asp_program())
        return

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
