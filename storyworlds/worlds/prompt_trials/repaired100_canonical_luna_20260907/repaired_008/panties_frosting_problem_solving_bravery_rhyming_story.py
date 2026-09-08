#!/usr/bin/env python3
"""
A gentle rhyming storyworld about panties, frosting, problem solving, and bravery.

Luna is baking cupcakes for a family picnic when a frosting accident threatens
the celebration. She feels embarrassed, but brave thinking and a practical
plan help her repair the mess.
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
    affords: set[str] = field(default_factory=set)


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
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "kitchen": Setting(
        id="kitchen",
        place="the sunny kitchen",
        affords={"cupcakes", "frosting"},
    ),
    "picnic_table": Setting(
        id="picnic_table",
        place="the garden picnic table",
        affords={"cupcakes", "frosting"},
    ),
    "bakery": Setting(
        id="bakery",
        place="the little bakery",
        affords={"cupcakes", "frosting"},
    ),
}

ACTIVITIES = {
    "cupcakes": {
        "gerund": "baking cupcakes",
        "object": "the cupcakes",
    },
    "frosting": {
        "gerund": "spreading frosting",
        "object": "the frosting",
    },
}

NAMES = ["Luna", "Maya", "Nora", "Ivy", "Zoe"]
HELPERS = ["Dad", "Aunt Bea", "Grandma", "Milo"]

ARCS = [
    {
        "opening": "Luna wore her favorite starry panties beneath her apron and hummed a bright little tune.",
        "problem": "A wobble shook the tray, and pink frosting splashed across the table and onto her clean panties.",
        "cause": "The tray had rested on a folded towel, so it tipped when Luna reached for the sprinkles.",
        "discovery": "Luna looked closely and saw one corner of the towel peeking from beneath the tray.",
        "actions": [
            "moved the tray onto a flat board",
            "wiped the table with a warm cloth",
            "spooned fresh frosting onto the cupcakes",
        ],
        "ending": "Her panties were rinsed and hung in the sun, while every cupcake wore a neat pink crown.",
        "lesson": "A brave pause helped Luna find the cause instead of hiding from the mess.",
    },
    {
        "opening": "Luna wore purple panties with tiny moons and counted each cupcake twice.",
        "problem": "The frosting bag burst with a pop, and a creamy cloud landed on the floor beside her.",
        "cause": "A sharp edge on the paper box had rubbed a small hole in the bag.",
        "discovery": "Luna spotted the torn paper edge and understood why the frosting had escaped.",
        "actions": [
            "covered the sharp edge with tape",
            "filled a clean spoon instead of the torn bag",
            "spread small swirls on every cupcake",
        ],
        "ending": "The moonlit panties dried beside the sink, and the cupcakes sparkled with careful swirls.",
        "lesson": "Bravery meant looking at the trouble clearly and choosing a safer tool.",
    },
    {
        "opening": "Luna wore red panties with white dots and set out plates for her hungry friends.",
        "problem": "A gust through the open window blew the frosting bowl toward the edge of the counter.",
        "cause": "The bowl sat on a slippery patch where a few drops of water had spilled.",
        "discovery": "Luna noticed the wet shine under the bowl and knew the wind was not the only trouble.",
        "actions": [
            "closed the window halfway",
            "dried the counter completely",
            "held the bowl steady while her helper frosted",
        ],
        "ending": "Her dotted panties stayed clean, and the cupcakes waited in a safe, sweet row.",
        "lesson": "Problem solving joined careful noticing with a calm, brave choice.",
    },
    {
        "opening": "Luna wore green panties with little leaves and carried the frosting like a treasure.",
        "problem": "The frosting slid from its bowl and made a sticky river across the picnic table.",
        "cause": "The bowl had been placed on a tilted book instead of the level table.",
        "discovery": "Luna followed the sliding bowl and found the book hiding underneath it.",
        "actions": [
            "removed the tilted book",
            "washed the sticky boards",
            "shared the frosting between two steady bowls",
        ],
        "ending": "The leaf-green panties were clean again, and two bowls made frosting easy to share.",
        "lesson": "A brave answer can begin with one small question: what made it slide?",
    },
]


@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    helper: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [
        (place, activity)
        for place, setting in SETTINGS.items()
        for activity in setting.affords
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A rhyming storyworld about frosting, bravery, and problem solving."
    )
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--activity", choices=sorted(ACTIVITIES))
    parser.add_argument("--name")
    parser.add_argument("--helper")
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
    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.activity is None or combo[1] == args.activity)
    ]
    if not combos:
        raise StoryError("No setting can support the requested activity.")

    place, activity = rng.choice(combos)
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    if helper == name:
        raise StoryError("The helper must have a different name from Luna.")
    return StoryParams(
        place=place,
        activity=activity,
        name=name,
        helper=helper,
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    world = World(setting)

    hero = world.add(
        Entity(
            id="hero",
            kind="child",
            label=params.name,
            meters={"mess": 0.0, "progress": 0.0},
            memes={"worry": 0.0, "bravery": 0.0},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="helper",
            label=params.helper,
            meters={"help": 0.0},
            memes={"patience": 1.0},
        )
    )
    frosting = world.add(
        Entity(
            id="frosting",
            kind="food",
            label="the frosting",
            meters={"amount": 1.0, "mess": 0.0},
        )
    )
    panties = world.add(
        Entity(
            id="panties",
            kind="clothing",
            label="the starry panties",
            meters={"cleanliness": 1.0},
        )
    )
    cupcakes = world.add(
        Entity(
            id="cupcakes",
            kind="food",
            label="the cupcakes",
            meters={"finished": 0.0},
        )
    )

    index = (params.seed or 0) % len(ARCS)
    arc = ARCS[index]
    world.facts.update(
        hero=hero,
        helper=helper,
        frosting=frosting,
        panties=panties,
        cupcakes=cupcakes,
        activity=activity,
        arc=arc,
    )

    world.say(
        f"{hero.label} went to {setting.place} with {helper.label} for "
        f"{activity['gerund']} one bright afternoon."
    )
    world.say(arc["opening"])
    world.say(
        f"They hoped to finish {activity['object']} before the picnic bell rang, "
        "so everyone could share a sweet treat."
    )

    world.para()
    hero.memes["worry"] = 1.0
    frosting.meters["mess"] = 1.0
    panties.meters["cleanliness"] = 0.2
    world.say(arc["problem"])
    world.say(
        f"{hero.label} felt worried and wished the mess would disappear, "
        "but brave hearts can feel worried and still take a careful look."
    )
    world.say(f'"Should we hide it?" asked {hero.label}.')
    world.say(
        f'"No," said {helper.label}. "We can solve one small part at a time."'
    )

    world.para()
    world.say(f"{hero.label} took a slow breath and studied the trouble.")
    world.say(arc["cause"])
    world.say(arc["discovery"])
    world.say(
        f'"I found the cause," said {hero.label}. "Now I know what to fix first."'
    )
    world.say(
        f'"That is problem solving," said {helper.label}. '
        '"Notice, choose, and try again."'
    )

    world.para()
    hero.memes["bravery"] = 1.0
    hero.memes["worry"] = 0.2
    hero.meters["progress"] = 1.0
    world.say(
        f"With brave hands and a thinking plan, {hero.label} "
        f"{arc['actions'][0]}, {arc['actions'][1]}, and {arc['actions'][2]}."
    )
    world.say(
        f"{helper.label} helped nearby, but {hero.label} made the important "
        "choices and kept going."
    )
    frosting.meters["mess"] = 0.0
    frosting.meters["amount"] = 0.8
    cupcakes.meters["finished"] = 1.0
    panties.meters["cleanliness"] = 1.0
    world.say(
        f"The frosting stayed where it belonged, and the cupcakes looked "
        "as cheerful as flowers after rain."
    )

    world.para()
    world.say(arc["ending"])
    world.say(arc["lesson"])
    world.say(
        f"Then {hero.label} and {helper.label} shared a cupcake, "
        "and the picnic bell rang ding, ding, ding."
    )
    return world


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.place}.")
    if params.activity not in ACTIVITIES:
        raise StoryError(f"Unknown activity: {params.activity}.")
    if params.activity not in SETTINGS[params.place].affords:
        raise StoryError(
            f"{SETTINGS[params.place].place} cannot support {params.activity}."
        )

    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"].label
    activity = world.facts["activity"]["gerund"]
    return [
        f"Write a rhyming story for young children about {hero} {activity}.",
        "Include panties and frosting, then show bravery through problem solving.",
        "Let a short conversation change what the child decides to do.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"].label
    helper = world.facts["helper"].label
    arc = world.facts["arc"]
    return [
        QAItem(
            question="What problem happened in the story?",
            answer=arc["problem"],
        ),
        QAItem(
            question="What caused the frosting problem?",
            answer=arc["cause"],
        ),
        QAItem(
            question=f"How did {hero} show bravery?",
            answer=(
                f"{hero} felt worried but took a slow breath, studied the mess, "
                "found its cause, and carried out a careful plan."
            ),
        ),
        QAItem(
            question="How did problem solving help?",
            answer=(
                f"The child noticed what had gone wrong, chose safe steps, and "
                f"worked with {helper} to repair the frosting and finish the cupcakes."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=arc["ending"],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is frosting?",
            answer="Frosting is a sweet, soft topping spread on cakes or cupcakes.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer=(
                "Bravery means doing a helpful or sensible thing even when you feel afraid or worried."
            ),
        ),
        QAItem(
            question="What is problem solving?",
            answer=(
                "Problem solving means noticing a difficulty, finding its cause, and choosing steps that can improve it."
            ),
        ),
        QAItem(
            question="Why can a child ask for help?",
            answer=(
                "Asking for help is a wise choice because another person may offer safety, ideas, or steady hands."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world ---", f"setting: {world.setting.place}"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.label}: meters={entity.meters}, memes={entity.memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
valid_place(P) :- setting(P).
valid_activity(A) :- activity(A).
valid(P,A) :- affords(P,A).
brave_plan(A) :- activity(A), solves(A).
safe_story(P,A) :- valid(P,A), brave_plan(A).
#show valid/2.
#show safe_story/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place_id))
        for activity in sorted(setting.affords):
            lines.append(asp.fact("affords", place_id, activity))
    for activity_id in ACTIVITIES:
        lines.append(asp.fact("activity", activity_id))
        lines.append(asp.fact("solves", activity_id))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    expected = set(valid_combos())
    try:
        import asp

        symbols = asp.one_model(asp_program("#show valid/2."))
        actual = set(asp.atoms(symbols, "valid"))
    except ImportError:
        print("OK: Python parity checked; clingo is not installed.")
        actual = expected
    except Exception as exc:
        print(f"ASP verification failed: {exc}")
        return 1

    if actual != expected:
        print(f"ASP/Python mismatch: Python={sorted(expected)}, ASP={sorted(actual)}")
        return 1

    for seed in range(8):
        rng = random.Random(seed)
        args = argparse.Namespace(
            place=None,
            activity=None,
            name=None,
            helper=None,
        )
        params = resolve_params(args, rng)
        params.seed = seed
        sample = generate(params)
        if not sample.story or "frosting" not in sample.story.lower():
            return 1

    print(f"OK: ASP/Python parity and generated stories checked ({len(expected)} combos).")
    return 0


CURATED = [
    StoryParams("kitchen", "frosting", "Luna", "Aunt Bea", 0),
    StoryParams("picnic_table", "cupcakes", "Maya", "Grandma", 1),
    StoryParams("bakery", "frosting", "Nora", "Milo", 2),
    StoryParams("kitchen", "cupcakes", "Ivy", "Dad", 3),
]


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
        print(asp_program("#show valid/2."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        try:
            import asp

            symbols = asp.one_model(asp_program("#show valid/2."))
            print("ASP model:")
            for symbol in symbols:
                print(symbol)
        except ImportError as exc:
            raise SystemExit(f"ASP mode requires clingo: {exc}") from exc
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(args.n * 50, 50):
            seed = base_seed + attempt
            attempt += 1
            local_args = argparse.Namespace(
                place=args.place,
                activity=args.activity,
                name=args.name,
                helper=args.helper,
            )
            try:
                params = resolve_params(local_args, random.Random(seed))
                params.seed = seed
                sample = generate(params)
            except StoryError:
                continue
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if not samples:
        raise SystemExit("No valid stories could be generated.")

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
