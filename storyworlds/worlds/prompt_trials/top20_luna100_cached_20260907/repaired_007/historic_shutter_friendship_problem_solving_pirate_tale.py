#!/usr/bin/env python3
"""
A small storyworld about friendship and problem solving aboard a historic ship.
A stubborn shutter hides the old harbor map, and two young pirates must listen,
test a safe plan, and work together before sunset.
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
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Place:
    id: str
    label: str
    historic: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class World:
    place: Place
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


@dataclass(frozen=True)
class Arc:
    key: str
    object_label: str
    problem: str
    method: str
    result: str
    opening: tuple[str, str]
    trouble: tuple[str, str]
    teamwork: tuple[str, str]
    ending: tuple[str, str]


ARCS = (
    Arc(
        "map_cabin",
        "brass shutter",
        "a brass shutter on the captain's cabin would not open",
        "one friend held the lantern while the other loosened salt-crusted hinges with warm oil",
        "the shutter opened and revealed the harbor map",
        (
            "On the historic ship Starling, Luna polished the wheel while Finn watched the tide.",
            "In the captain's cabin hung a brass shutter, older than any tale they had heard.",
        ),
        (
            "At sunset, the shutter jammed tight and hid the captain's harbor map.",
            '"A mighty pull may break it," said Finn. "We need a kinder plan."',
        ),
        (
            'Luna lifted the lantern. "Look closely," she said. "The hinges are white with salt."',
            'Finn smiled. "Then we will soften them first." Together they used warm oil and a small key.',
        ),
        (
            "The shutter opened with a creak, and the historic map shone beneath the lantern.",
            "The friends sailed safely by its marks, while Luna called, " + '"Best treasure is a clever friend!"',
        ),
    ),
    Arc(
        "lookout_window",
        "wooden shutter",
        "a wooden shutter at the lookout window had swollen in the rain",
        "one friend pressed the lower edge while the other tapped the frame gently with a rope-wrapped mallet",
        "the lookout window opened without cracking the old wood",
        (
            "On the historic deck of the Sea Finch, Luna counted gulls and Finn trimmed a blue sail.",
            "Their lookout window had a wooden shutter, painted with a faded golden star.",
        ),
        (
            "A rainy night had swollen the wood, so the shutter would not budge.",
            '"We must not smash an old thing," said Luna. "It has stories in its grain."',
        ),
        (
            '"I can press below," said Finn. "Can you tap the frame softly?"',
            "Luna wrapped the mallet in rope, and their gentle plan began.",
        ),
        (
            "The shutter eased open, and fresh sea air filled the lookout post.",
            "They spotted a safe channel together and waved to the historic ship below.",
        ),
    ),
    Arc(
        "chart_room",
        "iron shutter",
        "an iron shutter covered the tiny chart-room window",
        "one friend checked the latch while the other followed an old hinge mark with a copper pin",
        "the shutter swung free and let them read the storm chart",
        (
            "The historic pirate sloop Moon Kite rocked in a quiet cove.",
            "Luna sorted shells for the crew while Finn studied a locked iron shutter.",
        ),
        (
            "The shutter covered the chart-room window, and dark clouds gathered offshore.",
            '"We need the storm chart," said Finn. "But guessing could lead us onto rocks."',
        ),
        (
            '"Check the latch first," Luna replied. "I found a mark beside the hinge."',
            "Finn used a copper pin at the mark, and Luna held the lantern steady.",
        ),
        (
            "Click! The iron shutter swung free, and the storm chart showed a calm route.",
            "The friends thanked one another as their ship slipped safely beyond the rocks.",
        ),
    ),
    Arc(
        "old_lighthouse",
        "painted shutter",
        "a painted shutter at the historic lighthouse was stuck before the fog bell could be seen",
        "one friend brushed sand from the track while the other pulled the bell rope to shake loose a pebble",
        "the shutter slid aside and showed the bell's signal",
        (
            "At an historic lighthouse, Luna carried a coil of rope up the stone steps.",
            "Finn polished the brass bell while sea fog curled around the windows.",
        ),
        (
            "The painted shutter stuck halfway, hiding the bell's signal from their boat.",
            '"Pulling harder will tear the paint," Finn warned. "Let us find what blocks it."',
        ),
        (
            "Luna brushed sand from the lower track. Finn tugged the bell rope once.",
            "A pebble popped loose, and the friends pushed the shutter together.",
        ),
        (
            "The shutter slid open, and the bell gleamed through the fog.",
            "Their ship followed the signal home, guided by careful hands and loyal friendship.",
        ),
    ),
)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    helper_name: str
    hero_gender: str = "girl"
    helper_gender: str = "boy"
    seed: Optional[int] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


PLACES = {
    "starling": Place("starling", "the historic ship Starling"),
    "sea_finch": Place("sea_finch", "the historic ship Sea Finch"),
    "moon_kite": Place("moon_kite", "the historic pirate sloop Moon Kite"),
    "lighthouse": Place("lighthouse", "the historic harbor lighthouse"),
}

NAMES = {
    "girl": ["Luna", "Mara", "Nell", "Pia", "Ruby"],
    "boy": ["Finn", "Toby", "Jasper", "Kai", "Owen"],
}

CURATED = [
    StoryParams("starling", "Luna", "Finn"),
    StoryParams("sea_finch", "Mara", "Toby"),
    StoryParams("moon_kite", "Nell", "Jasper"),
    StoryParams("lighthouse", "Ruby", "Kai"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A pirate tale about a historic shutter and friendship.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--hero-gender", choices=list(NAMES))
    parser.add_argument("--helper-gender", choices=list(NAMES))
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
    hero_gender = args.hero_gender or "girl"
    helper_gender = args.helper_gender or "boy"
    hero = args.hero or rng.choice(NAMES[hero_gender])
    choices = [n for n in NAMES[helper_gender] if n != hero]
    helper = args.helper or rng.choice(choices)
    return StoryParams(
        place=args.place or rng.choice(list(PLACES)),
        hero_name=hero,
        helper_name=helper,
        hero_gender=hero_gender,
        helper_gender=helper_gender,
        seed=args.seed,
    )


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}.")
    if params.hero_name == params.helper_name:
        raise StoryError("The two friends must have different names.")
    if params.hero_gender not in NAMES or params.helper_gender not in NAMES:
        raise StoryError("Each sailor must have a supported gender.")

    rng = random.Random(params.seed if params.seed is not None else sum(ord(c) for c in params.place))
    arc = ARCS[rng.randrange(len(ARCS))]
    world = World(PLACES[params.place])
    hero = world.add(Entity(params.hero_name, "character", params.hero_gender, params.hero_name))
    helper = world.add(Entity(params.helper_name, "character", params.helper_gender, params.helper_name))
    shutter = world.add(Entity("shutter", "object", "shutter", arc.object_label))
    map_item = world.add(Entity("map", "object", "map", "harbor map"))

    hero.memes["curious"] = 1
    helper.memes["careful"] = 1
    shutter.meters["stuck"] = 1
    shutter.meters["historic"] = 1

    values = {"place": world.place.label, "hero": hero.label, "helper": helper.label}
    for line in arc.opening:
        world.say(line.format(**values))
    world.para()

    for line in arc.trouble:
        world.say(line.format(**values))
    world.para()

    hero.memes["brave"] += 1
    helper.memes["helpful"] += 1
    hero.meters["helped"] += 1
    helper.meters["helped"] += 1
    for line in arc.teamwork:
        world.say(line.format(**values))
    shutter.meters["stuck"] = 0
    shutter.meters["open"] = 1
    world.para()

    hero.memes["joy"] = 1
    helper.memes["joy"] = 1
    map_item.meters["revealed"] = 1
    for line in arc.ending:
        world.say(line.format(**values))

    world.facts.update(
        hero=hero,
        helper=helper,
        shutter=shutter,
        map=map_item,
        arc=arc,
        problem=arc.problem,
        method=arc.method,
        result=arc.result,
        ending=arc.ending[-1],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a child-friendly Pirate Tale using the words "historic" and "shutter".',
        f"Tell how {world.facts['hero'].label} and {world.facts['helper'].label} solve this problem through friendship: {world.facts['problem']}.",
        "Write a gentle sea adventure in which careful problem solving reveals a useful secret.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            "What problem did the friends face?",
            f"The friends faced this problem: {f['problem']}. The shutter hid something important, so they needed a safe plan.",
        ),
        QAItem(
            "How did friendship help them solve it?",
            f"They solved it through friendship because {f['method']}. Each friend took a different helpful part, and together {f['result']}.",
        ),
        QAItem(
            "What showed that their solution worked?",
            f"The ending showed the change: {f['ending']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a shutter?",
            "A shutter is a cover fitted over a window or opening. It can protect the opening or block light.",
        ),
        QAItem(
            "Why is friendship useful when solving a problem?",
            "Friendship helps because friends can listen, share ideas, and do different parts of a difficult job together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"  place: {world.place.id} (historic={world.place.historic})")
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
historic_place(P) :- place(P), historic(P).
stuck(S) :- shutter(S), stuck_meter(S,1).
friendship(H1,H2) :- hero(H1), helper(H2), H1 != H2.
solved(S) :- stuck(S), friendship(_, _), careful_plan.
revealed(map) :- solved(shutter).
#show solved/1.
#show revealed/1.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
        lines.append(asp.fact("historic", place))
    lines.extend(
        [
            asp.fact("shutter", "shutter"),
            asp.fact("stuck_meter", "shutter", 1),
            asp.fact("hero", "luna"),
            asp.fact("helper", "finn"),
            asp.fact("careful_plan"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(asp.atoms(model, "solved"))


def asp_verify() -> int:
    try:
        import asp

        model = asp.one_model(asp_program())
        if not asp.atoms(model, "solved"):
            print("ASP parity failed: shutter was not solved.")
            return 1
        sample = generate(StoryParams("starling", "Luna", "Finn", seed=3))
        if "historic" not in sample.story or "shutter" not in sample.story:
            print("Story smoke test failed: seed words missing.")
            return 1
        if sample.world.facts["shutter"].meters["open"] != 1:
            print("Python parity failed: shutter is not open.")
            return 1
    except Exception as exc:
        print(f"Verification failed: {exc}")
        return 1
    print("OK: smoke tests passed.")
    return 0


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
        print(asp_program("#show solved/1.\n#show revealed/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for index in range(max(1, args.n)):
            seed = base_seed + index
            local_args = argparse.Namespace(**vars(args))
            local_args.seed = seed
            params = resolve_params(local_args, random.Random(seed))
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
