#!/usr/bin/env python3
"""
A nursery-rhyme storyworld about smoke, friendship, and a skate park.

Luna wants to practice a new skate trick, but a smoky afternoon makes the
ramps hard to see. Her friend helps her slow down, share the space, and turn
a frightening cloud into a safe, bright lesson.
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
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
    setting: str = "skate park"
    name: str = "Luna"
    friend: str = "Milo"
    trick: str = "a bright little ollie"
    seed: Optional[int] = None


SETTINGS = {
    "skate_park": "the skate park",
}

NAMES = ["Luna", "Milo", "Pip", "Tess", "Nico", "Wren"]
TRICKS = [
    ("a bright little ollie", "jump over the low blue line"),
    ("a careful ramp roll", "roll up the small quarter pipe"),
    ("a moon-hop spin", "hop and turn beside the painted stars"),
]
FRIEND_WORDS = ["friend", "pal", "best buddy"]
SMOKE_SOURCES = [
    "a smoky food cart",
    "a smoky pile of leaves beyond the fence",
    "a smoky machine beside the maintenance shed",
]
RHYME_ENDINGS = [
    "slow and bright, we make things right",
    "hand in hand, we safely stand",
    "with a friend near, the path is clear",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A nursery rhyme about smoke, skating, and friendship."
    )
    parser.add_argument("--setting", choices=SETTINGS, default=None)
    parser.add_argument("--name", choices=NAMES, default=None)
    parser.add_argument("--friend", choices=NAMES, default=None)
    parser.add_argument("--trick", default=None)
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
    setting = args.setting or "skate_park"
    name = args.name or rng.choice(NAMES)
    choices = [n for n in NAMES if n != name]
    friend = args.friend or rng.choice(choices)
    trick = args.trick or rng.choice([item[0] for item in TRICKS])
    if friend == name:
        raise StoryError("The skater and friend must have different names.")
    return StoryParams(
        setting=setting,
        name=name,
        friend=friend,
        trick=trick,
    )


def choose_trick(params: StoryParams, rng: random.Random) -> tuple[str, str]:
    for label, motion in TRICKS:
        if label == params.trick:
            return label, motion
    if params.trick:
        raise StoryError(f"Unknown trick: {params.trick}")
    return rng.choice(TRICKS)


def tell(params: StoryParams, rng: random.Random) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.name == params.friend:
        raise StoryError("Friendship needs two different characters.")

    world = World(place=SETTINGS[params.setting])
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type="child",
            label=params.name,
            memes={"courage": 1.0, "worry": 0.0, "friendship": 1.0},
        )
    )
    friend = world.add(
        Entity(
            id="friend",
            kind="character",
            type="child",
            label=params.friend,
            memes={"care": 1.0, "friendship": 1.0},
        )
    )
    board = world.add(
        Entity(
            id="skateboard",
            kind="thing",
            type="skateboard",
            label="a little silver skateboard",
            owner="hero",
            meters={"speed": 0.0, "visibility_needed": 0.7},
        )
    )
    smoke = world.add(
        Entity(
            id="smoke",
            kind="thing",
            type="smoke",
            label="a gray ribbon of smoke",
            meters={"visibility": 0.35, "distance": 0.4},
            memes={"danger": 1.0},
        )
    )
    ramp = world.add(
        Entity(
            id="ramp",
            kind="place",
            type="ramp",
            label="the low blue ramp",
            meters={"visibility": 0.35, "safe": 0.0},
        )
    )

    trick, motion = choose_trick(params, rng)
    source = rng.choice(SMOKE_SOURCES)
    rhyme = rng.choice(RHYME_ENDINGS)

    world.say(
        f"At {world.place}, Luna's wheels went ring-a-ding-ding, while "
        f"{hero.label} dreamed of {trick}."
    )
    world.say(
        f"{hero.label} tapped {board.label} and sang, "
        f"\"I will {motion}, then sparkle and sing!\""
    )
    world.say(
        f"Then {source} sent a gray ribbon drifting over the ramps. "
        f"The smoke curled low, and the blue ramp became hard to see."
    )
    world.para()
    world.say(
        f"{friend.label} raised a hand and called, "
        f"\"Wait, {hero.label}! The ramp is hidden. Let's roll away and tell the park helper.\""
    )
    world.say(
        f"{hero.label} looked at the smoky path, then answered, "
        f"\"You are right, {friend.label}. A friend helps a friend make a safe choice.\""
    )
    hero.memes["worry"] = 1.0
    friend.memes["care"] += 1.0
    world.say(
        f"Together they carried {board.label} to the clear side of the park. "
        f"They told the helper, who stopped the source and opened the gate for fresh air."
    )
    smoke.meters["visibility"] = 0.9
    smoke.memes["danger"] = 0.0
    ramp.meters["visibility"] = 1.0
    ramp.meters["safe"] = 1.0
    board.meters["speed"] = 0.0
    world.say(
        f"When the smoke thinned to a pale little curl, {hero.label} and {friend.label} "
        f"returned to the ramp. {hero.label} tried the trick slowly, while {friend.label} "
        f"clapped a steady beat: \"{rhyme}!\""
    )
    world.say(
        f"The wheels kissed the ground with a soft click. The two friends shared the ramp, "
        f"shared the cheer, and left the park smiling under the clean blue sky."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        board=board,
        smoke=smoke,
        ramp=ramp,
        trick=trick,
        motion=motion,
        source=source,
        rhyme=rhyme,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a nursery rhyme about {f['hero'].label} and {f['friend'].label} "
        f"at the skate park when smoke hides a ramp.",
        "Tell a child-friendly story where friendship changes a risky skating plan.",
        "Use smoke, a skateboard, a helpful friend, and a safe happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Why did {f['hero'].label} stop skating at first?",
            answer=(
                f"{f['hero'].label} stopped because smoke drifted over the skate park "
                f"and hid the low blue ramp. {f['friend'].label} noticed the danger and "
                "helped choose a safer place."
            ),
        ),
        QAItem(
            question=f"How did {f['friend'].label} show friendship?",
            answer=(
                f"{f['friend'].label} spoke up kindly, moved away from the smoky ramp "
                "with the skateboard, and told the park helper so the air could clear."
            ),
        ),
        QAItem(
            question=f"What changed before {f['hero'].label} tried the trick?",
            answer=(
                f"The smoke thinned, the ramp became visible and safe, and "
                f"{f['hero'].label} tried {f['trick']} slowly while "
                f"{f['friend'].label} cheered."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is smoke?",
            answer=(
                "Smoke is a cloud of tiny particles and gases made when something burns "
                "or is heated."
            ),
        ),
        QAItem(
            question="Why should skaters wait when they cannot see a ramp?",
            answer=(
                "They should wait because clear sight helps them notice obstacles and "
                "move safely."
            ),
        ),
        QAItem(
            question="What does friendship mean in this story?",
            answer=(
                "Friendship means caring about someone, speaking honestly, and helping "
                "that person make a safe choice."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.extend(["", "== story QA =="])
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.extend(["", "== world QA =="])
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
required_word(smoke).
required_feature(friendship).
setting(skate_park).
style(nursery_rhyme).
safe_after_waiting.
valid_story :- required_word(smoke), required_feature(friendship),
                setting(skate_park), style(nursery_rhyme), safe_after_waiting.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("word", "smoke"),
            asp.fact("feature", "friendship"),
            asp.fact("setting", "skate_park"),
            asp.fact("style", "nursery_rhyme"),
            asp.fact("safe_after_waiting"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/0."))
    atoms = {str(atom) for atom in model}
    if "valid_story" in atoms:
        print("OK: ASP story constraints are satisfied.")
        return 0
    print("MISMATCH: ASP story constraints are not satisfied.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params, random.Random(params.seed))
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
        print("\n-- trace --")
        for entity in sample.world.entities.values():
            print(
                f"{entity.id}: type={entity.type} label={entity.label} "
                f"owner={entity.owner} meters={entity.meters} memes={entity.memes}"
            )
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        raise SystemExit(asp_verify())
    if args.show_asp or args.asp:
        print(asp_program("#show valid_story/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for name in NAMES:
            friend = next(item for item in NAMES if item != name)
            for trick, _ in TRICKS:
                params = StoryParams(
                    setting="skate_park",
                    name=name,
                    friend=friend,
                    trick=trick,
                    seed=base_seed,
                )
                samples.append(generate(params))
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
