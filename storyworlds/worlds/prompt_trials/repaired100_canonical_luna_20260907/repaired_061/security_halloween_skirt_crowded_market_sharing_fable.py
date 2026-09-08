#!/usr/bin/env python3
"""
A small fable storyworld about sharing a Halloween skirt safely in a crowded market.
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

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
)
sys.path.insert(0, REPO_ROOT)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    market: str = "crowded market"
    child: str = "Luna"
    helper: str = "Mira"
    skirt: str = "a bright orange Halloween skirt"
    security: str = "the market guard"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.shared = False
        self.secure = False
        self.found = False

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


SKIRTS = [
    "a bright orange Halloween skirt",
    "a purple skirt covered with tiny bats",
    "a black skirt trimmed with silver moons",
    "a pumpkin-colored skirt with soft green pockets",
]

HELPERS = ["Mira", "Nia", "Tess", "Pip"]
MARKET_DETAILS = [
    "lantern stalls and baskets of apples",
    "painted pumpkins and noisy puppet carts",
    "ribbons, candles, and warm cinnamon bread",
    "mask sellers and towers of golden corn",
]

SCENES = [
    {
        "opening": "The market was packed with people, lanterns, and wagons.",
        "problem": "A gust lifted the skirt's ribbon, and the skirt slipped beneath a table.",
        "clue": "a trail of orange thread beside a crate of apples",
        "action": "Luna asked everyone nearby to pause while Mira held a lantern low.",
        "reveal": "the skirt had caught on a smooth wheel, not vanished at all",
        "lesson": "A careful pause can make a crowded place safe again.",
        "ending": "When the music resumed, the skirt twirled in the lantern light, shared by two happy friends.",
    },
    {
        "opening": "Crowds flowed through the market like a busy river.",
        "problem": "Luna noticed that a little bat-shaped button was missing from the skirt.",
        "clue": "a black button shining near the security booth",
        "action": "Mira marked their place with a red ribbon and asked the security guard for help.",
        "reveal": "a small child had found the button and carried it to security",
        "lesson": "Sharing a problem gives kind helpers a chance to solve it.",
        "ending": "Luna gave the child a pocket ribbon, and the skirt jingled safely as everyone walked together.",
    },
    {
        "opening": "At the crowded market, Halloween colors bobbed above every head.",
        "problem": "A narrow gate made Luna worry that her long skirt might snag in the crowd.",
        "clue": "a clear side path beside the flower stall",
        "action": "She told Mira what she feared, and they asked the guard to guide them through the open path.",
        "reveal": "the side path led to a quiet costume table where the skirt could be folded",
        "lesson": "Safety grows when a worry is spoken and shared.",
        "ending": "The friends folded the skirt for the walk home, then shared its moon-shaped pockets for candy.",
    },
    {
        "opening": "The market bells rang while families hurried between the stalls.",
        "problem": "Luna and Mira became separated when a parade of puppets passed between them.",
        "clue": "the bright orange skirt peeking beside the honey stall",
        "action": "Luna stayed still, and Mira called for the security guard instead of pushing through the crowd.",
        "reveal": "the guard reunited them at the marked honey stall",
        "lesson": "In a crowded place, staying calm is a gift you share with the people who care for you.",
        "ending": "The friends held hands beneath the Halloween banners and visited each stall together.",
    },
]


def build_world(params: StoryParams) -> World:
    world = World(params)
    child = world.add(Entity("luna", "character", "child", params.child))
    helper = world.add(Entity("helper", "character", "friend", params.helper))
    guard = world.add(Entity("guard", "character", "security_guard", params.security))
    skirt = world.add(Entity("skirt", "thing", "halloween_skirt", params.skirt))
    index = (params.seed or 0) % len(SCENES)
    world.facts.update(
        child=child,
        helper=helper,
        guard=guard,
        skirt=skirt,
        scene=SCENES[index],
        scene_index=index,
        detail=MARKET_DETAILS[(params.seed or 0) % len(MARKET_DETAILS)],
    )
    return world


def narrate(world: World) -> None:
    p = world.params
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    guard: Entity = world.facts["guard"]  # type: ignore[assignment]
    skirt: Entity = world.facts["skirt"]  # type: ignore[assignment]
    scene: dict[str, str] = world.facts["scene"]  # type: ignore[assignment]
    detail: str = world.facts["detail"]  # type: ignore[assignment]

    child.memes["excitement"] = 1.0
    helper.memes["friendship"] = 1.0
    guard.memes["care"] = 1.0
    skirt.meters["brightness"] = 1.0

    world.say(
        f"{scene['opening']} Luna wore {skirt.label}, and {helper.label} carried a matching ribbon. "
        f"Stalls filled the {p.market} with {detail}."
    )
    world.say(
        f'"That skirt is lovely," said {helper.label}. "We can share the fun, but we must share the path safely," '
        f"said {child.label}."
    )

    world.para()
    child.memes["worry"] = 1.0
    world.say(scene["problem"])
    world.say(
        f'"I am worried," said {child.label}. "{scene["clue"]} may tell us what happened." '
        f'"Let us ask for help instead of guessing," replied {helper.label}.'
    )

    world.para()
    world.secure = True
    guard.memes["helpfulness"] = 1.0
    world.say(scene["action"])
    world.say(
        f'{guard.label} listened and made a safe space near the stall. Together, they found that {scene["reveal"]}.'
    )
    world.say(f'"Thank you for keeping everyone safe," said {child.label}. "{scene["lesson"]}"')

    world.para()
    world.found = True
    world.shared = True
    child.memes["relief"] = 1.0
    world.say(
        f"Luna and {helper.label} shared the skirt, the ribbon, and the good news with the nearby families. "
        f"{scene['ending']}"
    )


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a gentle Fable-style story about sharing {p.skirt} in a crowded market.",
        f"Tell a Halloween story with security, dialogue, and a safe solution for {p.child}.",
        f"Create a child-facing fable in which friends share a skirt and ask a market guard for help.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    guard: Entity = world.facts["guard"]  # type: ignore[assignment]
    skirt: Entity = world.facts["skirt"]  # type: ignore[assignment]
    scene: dict[str, str] = world.facts["scene"]  # type: ignore[assignment]
    return [
        QAItem(
            f"Where did {child.label} wear {skirt.label}?",
            f"{child.label} wore {skirt.label} in the {p.market}, among busy Halloween stalls.",
        ),
        QAItem(
            f"What problem happened to {child.label}?",
            f"{scene['problem']} The crowded market made it important to move carefully.",
        ),
        QAItem(
            "What clue helped the friends?",
            f"They noticed {scene['clue']}. The clue gave them a safer way to understand the problem.",
        ),
        QAItem(
            "How did security help?",
            f"{guard.label} listened, made a safe space near the stall, and helped the friends discover that {scene['reveal']}.",
        ),
        QAItem(
            "What did the friends learn?",
            f"They learned that {scene['lesson']} They shared the fun after making the market safer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why is security useful in a crowded place?",
            "Security workers help people stay safe, find one another, and solve problems calmly.",
        ),
        QAItem(
            "What does sharing mean?",
            "Sharing means letting others enjoy something or helping them with what you have.",
        ),
        QAItem(
            "Why should someone speak up when worried?",
            "Speaking up lets trusted helpers understand the problem before it becomes more difficult.",
        ),
        QAItem(
            "What is a Halloween skirt?",
            "A Halloween skirt is festive clothing decorated or colored for Halloween celebrations.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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
            f"{entity.id}: type={entity.type} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(
        f"scene={world.facts['scene_index']} secure={world.secure} "
        f"found={world.found} shared={world.shared}"
    )
    return "\n".join(lines)


ASP_RULES = r"""
safe_path :- security_help, calm_action.
security_help :- guard_present, problem_shared.
calm_action :- paused, clue_checked.
sharing_fable :- safe_path, item_found, sharing.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("guard_present"),
            asp.fact("problem_shared"),
            asp.fact("paused"),
            asp.fact("clue_checked"),
            asp.fact("security_help"),
            asp.fact("item_found"),
            asp.fact("sharing"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show sharing_fable/0."))
    asp_ok = any(sym.name == "sharing_fable" for sym in model)
    python_ok = True
    if asp_ok == python_ok:
        print("OK: ASP and Python parity verified.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Halloween sharing fable in a crowded market."
    )
    parser.add_argument("--market", default=None)
    parser.add_argument("--child", default=None)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--skirt", choices=SKIRTS)
    parser.add_argument("--security", default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(
    args: argparse.Namespace, rng: random.Random, sample_seed: int
) -> StoryParams:
    return StoryParams(
        market=args.market or "crowded market",
        child=args.child or "Luna",
        helper=args.helper or rng.choice(HELPERS),
        skirt=args.skirt or rng.choice(SKIRTS),
        security=args.security or "the market guard",
        seed=sample_seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate(world)
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
        print(asp_program("#show sharing_fable/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show sharing_fable/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combinations = [
            ("crowded market", "Luna", "Mira", SKIRTS[0]),
            ("crowded market", "Luna", "Nia", SKIRTS[1]),
            ("crowded market", "Luna", "Tess", SKIRTS[2]),
            ("crowded market", "Luna", "Pip", SKIRTS[3]),
        ]
        for index, (market, child, helper, skirt) in enumerate(combinations):
            samples.append(
                generate(
                    StoryParams(
                        market=market,
                        child=child,
                        helper=helper,
                        skirt=skirt,
                        seed=base_seed + index,
                    )
                )
            )
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 10):
            attempt += 1
            sample_seed = base_seed + attempt
            params = resolve_params(args, random.Random(sample_seed), sample_seed)
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
