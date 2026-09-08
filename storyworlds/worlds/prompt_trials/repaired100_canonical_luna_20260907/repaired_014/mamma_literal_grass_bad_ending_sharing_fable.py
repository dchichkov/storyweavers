#!/usr/bin/env python3
"""
A small fable about Mamma, a literal promise, a patch of grass, and the
difference between sharing a thing and sharing its care.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "the village green"
    affords: set[str] = field(
        default_factory=lambda: {"sit", "play", "plant", "share", "water"}
    )


@dataclass
class StoryParams:
    child_name: str
    friend_name: str
    mamma_name: str
    grass: int = 0
    promise: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class GrassPatch:
    name: str
    color: str
    trouble: str
    repair: str
    image: str


GRASS_PATCHES = [
    GrassPatch(
        "the soft green patch",
        "green",
        "a bare brown ring appeared where everyone had trampled the blades",
        "marked two paths around the patch and watered the tired roots",
        "the grass lifted its bright blades again",
    ),
    GrassPatch(
        "the little meadow beside the well",
        "emerald",
        "the thirsty grass curled beneath the hot sun",
        "shared the bucket in small, careful turns",
        "cool drops shone like beads on every blade",
    ),
    GrassPatch(
        "the clover grass by the old gate",
        "green and white",
        "the clover was crushed under too many visiting feet",
        "made a stepping path and left the flowers room to grow",
        "bees hummed above the unbroken clover",
    ),
    GrassPatch(
        "the long grass under the apple tree",
        "gold-tipped green",
        "a careless pile of blankets had flattened the grass",
        "lifted the blankets and shared the shady resting place",
        "the grass stood softly beneath the apple tree",
    ),
]

PROMISES = [
    (
        "Mamma said, 'The green is for everyone,'",
        "I will share every blade",
        "the child took the words literally and tried to hand pieces of grass to everyone",
    ),
    (
        "Mamma said, 'Let the grass belong to all of us,'",
        "I will give it away",
        "the child thought belonging meant cutting the grass into little gifts",
    ),
    (
        "Mamma said, 'Share the meadow kindly,'",
        "I will make every visitor equal",
        "the child invited everyone to stand wherever they wished, even on the young shoots",
    ),
]

ENDINGS = [
    (
        "A promise needs a wise meaning as well as faithful words.",
        "The children shared the meadow by sharing its care.",
    ),
    (
        "Kindness is not giving away what cannot speak; it is making room for life.",
        "The children learned to share a place without harming the life inside it.",
    ),
    (
        "A literal answer can miss the heart of a loving request.",
        "The children listened for Mamma's meaning before they acted.",
    ),
]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

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


def build_story(params: StoryParams) -> World:
    patch = GRASS_PATCHES[params.grass % len(GRASS_PATCHES)]
    promise = PROMISES[params.promise % len(PROMISES)]
    ending = ENDINGS[params.ending % len(ENDINGS)]
    setting = Setting()
    world = World(setting)

    child = world.add(
        Entity(
            "Child",
            "character",
            "child",
            params.child_name,
            memes={"eager": 1.0, "understanding": 0.0},
        )
    )
    friend = world.add(
        Entity(
            "Friend",
            "character",
            "child",
            params.friend_name,
            memes={"helpful": 1.0},
        )
    )
    mamma = world.add(
        Entity(
            "Mamma",
            "character",
            "mother",
            params.mamma_name,
            memes={"patient": 1.0},
        )
    )
    grass = world.add(
        Entity(
            "Grass",
            "plant",
            "grass",
            patch.name,
            meters={"green": 1.0, "trampled": 0.0, "water": 0.0},
            memes={"shared": 0.0, "safe": 0.0},
        )
    )

    world.facts.update(
        child=child,
        friend=friend,
        mamma=mamma,
        grass=grass,
        patch=patch,
        promise=promise,
        ending=ending,
    )

    world.say(
        f"On {setting.place}, {mamma.label} watched {child.label} admire {patch.name}. "
        f"Its {patch.color} blades shone beside the dusty road."
    )
    world.say(
        f'"Mamma, may I keep it?" asked {child.label}. '
        f'{mamma.label} smiled and said, "{promise[0]} It must be cared for."'
    )
    child.memes["understanding"] = 0.0
    world.para()

    world.say(
        f"{child.label} heard only the plainest part of the sentence. "
        f"{promise[1].capitalize()}, {child.label} decided."
    )
    world.say(
        f"With a small basket and a very serious face, {child.label} began to act: "
        f"{promise[2]}."
    )
    grass.meters["trampled"] = 1.0
    world.fired.add("literal_mistake")
    world.say(
        f"By noon, {patch.trouble}. The green place no longer looked ready for play."
    )
    world.para()

    world.say(
        f'{friend.label} hurried over. "{child.label}, sharing does not mean hurting the thing we share," '
        f"{friend.label} said."
    )
    world.say(
        f'"But Mamma said it was for everyone," {child.label} replied. '
        f'"Then everyone must help it live," said {friend.label}.'
    )
    child.memes["understanding"] = 1.0
    world.say(
        f"{mamma.label} knelt beside them. She explained that grass could not answer for itself, "
        "so kindness had to protect it as well as welcome people."
    )
    world.para()

    world.say(
        f"Together they chose a gentler plan. They {patch.repair}."
    )
    grass.meters["trampled"] = 0.0
    grass.meters["water"] = 1.0
    grass.memes["shared"] = 1.0
    grass.memes["safe"] = 1.0
    world.fired.add("care_shared")
    world.say(
        f"{child.label} made room for games, {friend.label} watched the path, and "
        f"{mamma.label} showed them how to notice small growing things."
    )
    world.say(
        f"But the first careless choice had a cost: {patch.trouble.capitalize()}, "
        "and some of the young plants would not return that day."
    )
    world.say(
        f"{ending[0]} {ending[1]} {patch.image.capitalize()}."
    )
    world.facts["lesson"] = ending[0]
    return world


def generation_prompts(world: World) -> list[str]:
    patch: GrassPatch = world.facts["patch"]  # type: ignore[assignment]
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    return [
        f"Write a child-friendly fable about {child.label}, Mamma, and grass on the village green.",
        f"Show how a literal understanding of sharing harms {patch.name} before care repairs the mistake.",
        "End with a gentle but honest bad ending: some damage remains, while the characters learn how to share wisely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    mamma: Entity = world.facts["mamma"]  # type: ignore[assignment]
    patch: GrassPatch = world.facts["patch"]  # type: ignore[assignment]
    ending = world.facts["ending"]  # type: ignore[assignment]
    return [
        QAItem(
            f"What did {mamma.label} mean when she said the grass was for everyone?",
            f"{mamma.label} meant that everyone could enjoy the grass while helping protect it. She did not mean that {child.label} should tear it up or give away its blades.",
        ),
        QAItem(
            f"Why did {patch.name} become damaged?",
            f"It became damaged because {child.label} understood the sharing request too literally and let people use the grass without making room for its roots and young plants.",
        ),
        QAItem(
            f"How did {child.label} and {friend.label} repair the mistake?",
            f"They listened to {mamma.label}, made a gentler plan, protected the growing area, and shared the work of caring for the grass.",
        ),
        QAItem(
            "What is the fable's lesson?",
            f"{ending[0]} The children learned that sharing a place also means caring for the life that makes the place special.",
        ),
        QAItem(
            "Why is the ending partly bad?",
            f"The ending is partly bad because the careful plan helps the grass, but some young plants were already harmed and could not return that day.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is grass?",
            "Grass is a green plant with narrow blades that often grows in fields, yards, and meadows.",
        ),
        QAItem(
            "What does sharing mean?",
            "Sharing means allowing others to use or enjoy something while treating it fairly and taking care of it.",
        ),
        QAItem(
            "What does literal mean?",
            "Literal means taking words in their most exact, direct sense instead of looking for a broader intended meaning.",
        ),
        QAItem(
            "What is a fable?",
            "A fable is a short story, sometimes with talking animals or simple characters, that teaches a lesson.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:8} ({entity.type:8}) meters={meters} memes={memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("topic", "mamma"),
            asp.fact("topic", "literal"),
            asp.fact("topic", "grass"),
            asp.fact("feature", "bad_ending"),
            asp.fact("feature", "sharing"),
            asp.fact("setting", "village_green"),
            asp.fact("affords", "village_green", "share"),
            asp.fact("affords", "village_green", "water"),
            asp.fact("affords", "village_green", "plant"),
        ]
    )


ASP_RULES = r"""
topic(mamma).
topic(literal).
topic(grass).
feature(bad_ending).
feature(sharing).
setting(village_green).

care_required(grass).
literal_mistake(literal).
repair_possible(sharing) :- care_required(grass).
lesson_present(bad_ending) :- literal_mistake(literal), repair_possible(sharing).
story_ok :- topic(mamma), topic(literal), topic(grass),
             feature(bad_ending), feature(sharing),
             setting(village_green), lesson_present(bad_ending).

#show story_ok/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show story_ok/0."))
    ok = any(symbol.name == "story_ok" for symbol in model)
    if not ok:
        print("MISMATCH: ASP twin failed.")
        return 1
    for index in range(len(GRASS_PATCHES)):
        params = StoryParams("Luna", "Pip", "Mamma", grass=index, promise=0, ending=0)
        sample = generate(params)
        if not sample.story or "grass" not in sample.story.lower():
            print("MISMATCH: generated story check failed.")
            return 1
    print("OK: ASP twin and generated stories agree.")
    return 0


CHILD_NAMES = ["Luna", "Milo", "Nia", "Toby", "Pia", "Owen"]
FRIEND_NAMES = ["Pip", "Rose", "Sam", "Ivy", "Ben", "Ada"]
MAMMA_NAMES = ["Mamma", "Mama June", "Mamma Rose"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A fable about Mamma, literal sharing, grass, and care."
    )
    parser.add_argument("--child-name")
    parser.add_argument("--friend-name")
    parser.add_argument("--mamma-name")
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
    return StoryParams(
        child_name=args.child_name or rng.choice(CHILD_NAMES),
        friend_name=args.friend_name or rng.choice(FRIEND_NAMES),
        mamma_name=args.mamma_name or rng.choice(MAMMA_NAMES),
        grass=rng.randrange(len(GRASS_PATCHES)),
        promise=rng.randrange(len(PROMISES)),
        ending=rng.randrange(len(ENDINGS)),
    )


def validate_params(params: StoryParams) -> None:
    if not params.child_name.strip():
        raise StoryError("child name must not be empty")
    if not params.friend_name.strip():
        raise StoryError("friend name must not be empty")
    if not params.mamma_name.strip():
        raise StoryError("mamma name must not be empty")
    if params.child_name.strip().lower() == params.friend_name.strip().lower():
        raise StoryError("child and friend must have different names")


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = build_story(params)
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
        print(asp_program("#show story_ok/0."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show story_ok/0."))
        print("story_ok" if any(s.name == "story_ok" for s in model) else "no model")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for grass in range(len(GRASS_PATCHES)):
            params = StoryParams(
                "Luna",
                "Pip",
                "Mamma",
                grass=grass,
                promise=grass % len(PROMISES),
                ending=grass % len(ENDINGS),
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        seen_shapes: set[tuple[int, int, int]] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(20, args.n * 20):
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            attempt += 1
            sample = generate(params)
            shape = (params.grass, params.promise, params.ending)
            if sample.story in seen or shape in seen_shapes:
                continue
            seen.add(sample.story)
            seen_shapes.add(shape)
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
