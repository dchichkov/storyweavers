#!/usr/bin/env python3
"""
A small slice-of-life storyworld about a child, a tambourine, and a little
snow pen built before winter settles in. The world tracks practical supplies
and emotional memories while foreshadowing a quiet problem that kindness solves.
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
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
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
    companion: str
    mood: str
    seed: Optional[int] = None


NAMES = ["Luna", "Mara", "Niko", "Tess", "Ivo", "Sana"]
COMPANIONS = ["her little brother Pip", "her neighbor Jo", "her friend Emi", "her cousin Ren"]
MOODS = ["curious", "careful", "cheerful", "quiet"]

SETTING = Setting(
    place="the small yard behind the village hall",
    affords={"dun", "tambourine", "snowpen", "music", "winter"},
)

OPENINGS = [
    "On an ordinary afternoon, {name} carried a tambourine into {place}.",
    "The last leaves skittered across {place} when {name} came outside with a tambourine under one arm.",
    "After lunch, {name} found a quiet patch of {place} and began making plans for the first snow.",
]

MORALS = [
    "A small welcome can make a cold day feel warm.",
    "Listening closely helps a friend feel safe.",
    "The best plans leave room for someone who is still finding their courage.",
]

@dataclass(frozen=True)
class Plan:
    animal: str
    trouble: str
    clue: str
    repair: str
    ending: str
    answer: str

PLANS = [
    Plan(
        animal="a shy white rabbit",
        trouble="a loose board had fallen across the little snow pen",
        clue="the board would slide farther when the first heavy snow came",
        repair="Luna and her companion lifted it together and tied it to the fence with red cloth",
        ending="When snow finally came, the rabbit slept safely inside the pen while the tambourine rested above the door",
        answer="A loose board had fallen across the snow pen.",
    ),
    Plan(
        animal="a tiny field mouse",
        trouble="the gate of the snow pen would not quite close",
        clue="a cold wind was already slipping through the gap",
        repair="Luna held the gate steady while her companion found a smooth stone to keep it shut",
        ending="The next morning, tiny tracks curved safely around the snug snow pen",
        answer="The snow pen's gate would not close.",
    ),
    Plan(
        animal="a young sparrow",
        trouble="the roof of the snow pen had a thin crack",
        clue="meltwater would drip through it after the first sunny day",
        repair="Luna pressed a piece of waxed cloth over the crack while her companion held the corners flat",
        ending="Sunlight later shone on the dry roof, and the tambourine made a soft silver sound nearby",
        answer="A thin crack ran across the roof of the snow pen.",
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        ("yard", "dun", "tambourine"),
        ("yard", "dun", "snowpen"),
        ("yard", "tambourine", "snowpen"),
    ]


def generation_prompts(world: World) -> list[str]:
    plan = world.facts["plan"]
    return [
        'Write a gentle slice-of-life story using "dun", "tambourine", and "snowpen".',
        f"Tell a quiet winter-preparation story about {world.facts['name']} and {world.facts['companion']}.",
        f"Include a small problem: {plan.trouble}, and solve it through careful listening.",
    ]


def story_questions(world: World) -> list[QAItem]:
    plan: Plan = world.facts["plan"]
    name = world.facts["name"]
    companion = world.facts["companion"]
    animal = plan.animal
    return [
        QAItem(
            question="Who prepared the snow pen?",
            answer=f"{name} and {companion} prepared the snow pen together.",
        ),
        QAItem(
            question="What problem did they notice?",
            answer=plan.answer,
        ),
        QAItem(
            question="What did the tambourine do in the story?",
            answer=f"{name} used the tambourine to mark a gentle rhythm while they worked.",
        ),
        QAItem(
            question="Why did the small clue matter?",
            answer=f"It warned them that {plan.clue}, so they repaired the snow pen before winter arrived.",
        ),
        QAItem(
            question="What happened at the end?",
            answer=f"{plan.ending}.",
        ),
        QAItem(
            question="What lesson did they learn?",
            answer=world.facts["moral"],
        ),
        QAItem(
            question="Who would use the snow pen?",
            answer=f"The snow pen was made ready for {animal}.",
        ),
    ]


def world_questions(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tambourine?",
            answer="A tambourine is a small musical instrument with a round frame that can be shaken or tapped.",
        ),
        QAItem(
            question="What is a snow pen?",
            answer="A snow pen is a small fenced shelter or enclosure prepared for safety during snowy weather.",
        ),
        QAItem(
            question="What does dun mean?",
            answer="Dun describes a muted gray-brown color, like dry grass or a quiet winter coat.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a small clue that hints at something important that may happen later.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private thought written inside the story.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"  setting: {world.setting.place}")
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:12} ({entity.type:8}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  fired: {sorted(world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("setting", "yard"),
        asp.fact("word", "dun"),
        asp.fact("word", "tambourine"),
        asp.fact("word", "snowpen"),
        asp.fact("tool", "tambourine"),
        asp.fact("place", "snowpen"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(yard, dun, tambourine) :- setting(yard), word(dun), tool(tambourine).
valid_story(yard, dun, snowpen) :- setting(yard), word(dun), place(snowpen).
valid_story(yard, tambourine, snowpen) :- setting(yard), tool(tambourine), place(snowpen).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = set(valid_combos())
    actual = set(asp_valid_combos())
    if expected == actual:
        print(f"OK: ASP gate matches Python gate ({len(actual)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    print("Only in ASP:", sorted(actual - expected))
    print("Only in Python:", sorted(expected - actual))
    return 1


def validate_params(params: StoryParams) -> None:
    if params.name not in NAMES:
        raise StoryError(f"Unknown name: {params.name}")
    if params.companion not in COMPANIONS:
        raise StoryError(f"Unknown companion: {params.companion}")
    if params.mood not in MOODS:
        raise StoryError(f"Unknown mood: {params.mood}")


def tell(params: StoryParams) -> World:
    validate_params(params)
    world = World(SETTING)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        label=params.name,
        type="child",
        meters={"energy": 1.0},
        memes={"curiosity": 1.0},
    ))
    companion = world.add(Entity(
        id="companion",
        kind="character",
        label=params.companion,
        type="companion",
        meters={"warmth": 1.0},
        memes={"trust": 1.0},
    ))
    tambourine = world.add(Entity(
        id="tambourine",
        kind="object",
        label="a tambourine",
        type="instrument",
        meters={"sound": 0.0},
        memes={"welcome": 0.0},
    ))
    pen = world.add(Entity(
        id="snowpen",
        kind="place",
        label="the snow pen",
        type="shelter",
        meters={"stability": 0.0},
        memes={"safety": 0.0},
    ))

    stable_seed = params.seed
    if stable_seed is None:
        stable_seed = sum((i + 1) * ord(c) for i, c in enumerate(
            f"{params.name}:{params.companion}:{params.mood}"
        ))
    rng = random.Random(stable_seed)
    plan = rng.choice(PLANS)
    moral = rng.choice(MORALS)

    world.facts.update(
        name=params.name,
        companion=params.companion,
        plan=plan,
        moral=moral,
        hero=hero,
        companion_entity=companion,
        tambourine=tambourine,
        pen=pen,
    )

    world.say(OPENINGS[rng.randrange(len(OPENINGS))].format(
        name=params.name,
        place=SETTING.place,
    ))
    world.say(
        f"The ground was a dun brown, and the air smelled of dry leaves. "
        f"{params.companion} came to help because the little {plan.animal} needed a safe place before snow."
    )
    world.say(
        f"{params.name} tapped the tambourine once: dun. "
        f"It was not a marching sound. It was a small sound for beginning."
    )
    world.para()

    world.say(f"Near the snow pen, {plan.trouble}.")
    world.say(
        f"{params.name} touched the wood and thought, \"I hope nobody notices this too late.\" "
        "The thought stayed quiet, but it made the next tap of the tambourine stop in the air."
    )
    world.say(
        f"\"Did you hear that?\" asked {params.name}. "
        f"\"I heard the gate whisper,\" said {params.companion}. "
        "\"Then we should listen before we fix it,\" {params.name} replied."
    )
    world.say(f"The small warning was clear: {plan.clue}.")
    world.para()

    hero.meters["energy"] = 0.7
    hero.memes["care"] = 1.0
    companion.memes["attention"] = 1.0
    tambourine.meters["sound"] = 1.0
    world.fired.add("foreshadowing_noticed")

    world.say(
        f"{params.name} played a soft rhythm while {params.companion} watched the snow pen. "
        "The rhythm gave their hands an easy pace."
    )
    world.say(f"{plan.repair}.")
    world.say(
        f"\"Now it feels ready,\" said {params.companion}. "
        f"\"Ready is better than hurried,\" {params.name} answered."
    )
    world.para()

    pen.meters["stability"] = 1.0
    pen.memes["safety"] = 1.0
    hero.memes["relief"] = 1.0
    companion.memes["pride"] = 1.0

    world.say(
        f"The {plan.animal} stayed near the fence, watching with bright, patient eyes. "
        f"{params.name} set the tambourine above the snow pen and brushed the dun dust from its rim."
    )
    world.say(f"{plan.ending}.")
    world.say(
        f"{params.name} smiled. The quiet thought had changed: not \"I hope nobody notices,\" "
        "but \"We noticed in time.\""
    )
    world.say(f"They carried that feeling home. {moral}")
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_questions(world),
        world_qa=world_questions(world),
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A slice-of-life snow pen story with a tambourine and quiet clues."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--mood", choices=MOODS)
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        companion=args.companion or rng.choice(COMPANIONS),
        mood=args.mood or rng.choice(MOODS),
    )


CURATED = [
    StoryParams("Luna", "her little brother Pip", "careful"),
    StoryParams("Mara", "her neighbor Jo", "curious"),
    StoryParams("Niko", "her friend Emi", "quiet"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(item) for item in CURATED]
    else:
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps(
                [sample.to_dict() for sample in samples],
                indent=2,
                ensure_ascii=False,
            ))
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
