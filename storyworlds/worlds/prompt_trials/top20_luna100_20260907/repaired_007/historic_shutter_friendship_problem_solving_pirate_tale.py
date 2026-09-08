#!/usr/bin/env python3
"""
A small storyworld about a historic shutter, pirate friends, and problem solving.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Place:
    id: str
    label: str
    tags: set[str] = field(default_factory=set)
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
    problem: str
    tool: str
    action: str
    result: str
    opening: tuple[str, str]
    trouble: tuple[str, str]
    plan: tuple[str, str]
    ending: tuple[str, str]


ARCS = (
    Arc(
        "salt_wind",
        "the salt wind had jammed one hinge of the historic shutter",
        "a coil of rope and a smooth bit of soap",
        "one friend held the shutter steady while the other soaped the hinge and pulled the rope",
        "the old window opened safely to the sea breeze",
        (
            "On the historic lighthouse at Gullrock Bay, Captain Luna and Mate Finn polished a brass spyglass.",
            "They watched for friendly sails while their little pirate flag snapped in the salty air.",
        ),
        (
            "Then the historic shutter slammed shut with a bang, and the lighthouse lantern went dark.",
            '"We must not yank it," said Finn. "A careful plan will help us, I think."',
        ),
        (
            '"I can hold the shutter," said Luna. "Can you reach the hinge with our rope and soap?"',
            '"Aye, together!" cried Finn. "You steady the wood, and I will make the stiff hinge move."',
        ),
        (
            "The hinge turned, the shutter swung wide, and warm sunlight spilled across the floor.",
            "Luna and Finn cheered as their friendship shone brighter than any treasure chest.",
        ),
    ),
    Arc(
        "hidden_map",
        "the historic shutter had covered the old map painted on the wall",
        "a lantern and a small wooden wedge",
        "one friend lifted the shutter while the other wedged it open and read the map",
        "the friends found the safe route to their harbor",
        (
            "At historic Coralwatch Fort, Luna and Finn searched for a harbor marked on an old pirate map.",
            "Their boots tapped the stone floor as gulls cried above the blue water.",
        ),
        (
            "A heavy shutter covered the map, and its lower edge stuck fast in the sand.",
            '"The route is hidden," said Luna. Finn frowned. "We need our wits, not a wild tug."',
        ),
        (
            "Finn shone the lantern low while Luna lifted the shutter with a wooden wedge.",
            '"Now I can see the compass rose!" cried Finn. "The map points home by the moonlit cove."',
        ),
        (
            "The friends followed the safe route and sailed home without meeting the rocky shoals.",
            "Their solved problem became a treasured tale told beside the friendly harbor fire.",
        ),
    ),
    Arc(
        "rainy_roof",
        "rain had swollen the historic shutter until it blocked the captain's room",
        "a bucket, a dry cloth, and a flat paddle",
        "one friend dried the wood while the other eased the swollen edge away from the frame",
        "the captain's room opened before the next tide",
        (
            "In the historic captain's house on Parrot Pier, Luna sorted shells while Finn counted coils of rope.",
            "A stormy cloud curled over the harbor like a gray pirate beard.",
        ),
        (
            "Rain swelled the old shutter tight against the room, trapping the captain's log inside.",
            '"The log must stay dry," said Finn. "Let us solve this before the next tide."',
        ),
        (
            "Luna caught the drips in a bucket and dried the wood while Finn slid in the flat paddle.",
            '"Slow and gentle," Luna said. "Aye," said Finn, "friends make a strong crew."',
        ),
        (
            "The shutter eased open, and the captain's log rested safely on a dry table.",
            "The storm passed while the friends shared warm cocoa and planned tomorrow's voyage.",
        ),
    ),
)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


PLACES = {
    "gullrock": Place("gullrock", "the historic lighthouse at Gullrock Bay", {"coast", "historic"}),
    "coralwatch": Place("coralwatch", "historic Coralwatch Fort", {"coast", "historic"}),
    "parrot_pier": Place("parrot_pier", "the historic captain's house on Parrot Pier", {"harbor", "historic"}),
}

NAMES = ["Luna", "Finn", "Pip", "Mara", "Theo", "Nell"]

CURATED = [
    StoryParams("gullrock", "Luna", "Finn", 11),
    StoryParams("coralwatch", "Mara", "Pip", 22),
    StoryParams("parrot_pier", "Theo", "Nell", 33),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A pirate tale about a historic shutter and friendship.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
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
    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or rng.choice(NAMES)
    choices = [name for name in NAMES if name != hero]
    helper = args.helper or rng.choice(choices)
    if hero == helper:
        raise StoryError("The pirate friends must have different names.")
    return StoryParams(place, hero, helper)


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError("Unknown setting.")
    if not params.hero_name.strip() or not params.helper_name.strip():
        raise StoryError("Both pirate friends need names.")
    if params.hero_name.casefold() == params.helper_name.casefold():
        raise StoryError("The two friends cannot share the same name.")

    rng = random.Random(params.seed)
    arc = ARCS[rng.randrange(len(ARCS))]
    world = World(PLACES[params.place])
    hero = world.add(Entity(params.hero_name, "character", "pirate", params.hero_name, "captain"))
    helper = world.add(Entity(params.helper_name, "character", "pirate", params.helper_name, "mate"))
    shutter = world.add(Entity("historic_shutter", "object", "shutter", "historic shutter"))
    shutter.meters["jammed"] = 1.0
    shutter.meters["opened"] = 0.0
    hero.memes["curiosity"] = 1.0
    helper.memes["courage"] = 1.0

    values = {"hero": params.hero_name, "helper": params.helper_name}
    for line in arc.opening:
        world.say(line.format(**values))
    world.para()
    for line in arc.trouble:
        world.say(line.format(**values))
    world.para()
    hero.memes["trust"] += 1.0
    helper.memes["trust"] += 1.0
    hero.meters["held"] = 1.0
    helper.meters["solved"] = 1.0
    for line in arc.plan:
        world.say(line.format(**values))
    shutter.meters["jammed"] = 0.0
    shutter.meters["opened"] = 1.0
    world.para()
    hero.memes["joy"] = 1.0
    helper.memes["joy"] = 1.0
    for line in arc.ending:
        world.say(line.format(**values))

    world.facts.update(
        hero=hero,
        helper=helper,
        shutter=shutter,
        place=world.place,
        arc=arc,
        problem=arc.problem,
        tool=arc.tool,
        action=arc.action,
        result=arc.result,
        ending=arc.ending[-1].format(**values),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a child-friendly Pirate Tale containing the words "historic" and "shutter".',
        f"Tell a pirate story in which {f['hero'].label} and {f['helper'].label} use friendship and problem solving after {f['problem']}.",
        f"Describe how the friends use {f['tool']} so that {f['result']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            "What problem did the pirate friends face?",
            f"They faced a problem because {f['problem']}. The historic shutter could not be used normally.",
        ),
        QAItem(
            "How did the friends solve the problem?",
            f"They solved it with friendship and problem solving: {f['action']}. They used {f['tool']}, and then {f['result']}.",
        ),
        QAItem(
            "What showed that their friendship mattered?",
            f"The final image showed the change: {f['ending']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a shutter?",
            "A shutter is a movable cover for a window or opening. It can help block light, wind, or rain.",
        ),
        QAItem(
            "What does historic mean?",
            "Historic means important in history or connected with the past.",
        ),
        QAItem(
            "Why can friendship help solve a problem?",
            "Friends can share ideas, encourage one another, and take different helpful actions together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(f"  {entity.id}: meters={meters}, memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
historic_shutter(S) :- shutter(S), historic(S).
can_open(S) :- historic_shutter(S), hinge_clear(S), friend_pair.
outcome(opened) :- can_open(S).
"""


def asp_facts() -> str:
    import asp
    facts = []
    for place in PLACES:
        facts.append(asp.fact("place", place))
    facts.extend(
        [
            asp.fact("shutter", "historic_shutter"),
            asp.fact("historic", "historic_shutter"),
            asp.fact("hinge_clear", "historic_shutter"),
            asp.fact("friend_pair"),
        ]
    )
    return "\n".join(facts)


def asp_program(show: str = "#show outcome/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
        if not asp.atoms(model, "outcome"):
            print("ASP verification failed: no opened outcome.")
            return 1
        sample = generate(StoryParams("gullrock", "Luna", "Finn", 1))
        if "historic" not in sample.story or "shutter" not in sample.story:
            print("Story verification failed: seed words missing.")
            return 1
        if len(sample.story_qa) < 3 or not sample.story.strip():
            print("Story verification failed: incomplete sample.")
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


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show outcome/1."))
        print(asp.atoms(model, "outcome"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        for index in range(max(args.n, 1)):
            seed = base_seed + index
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
