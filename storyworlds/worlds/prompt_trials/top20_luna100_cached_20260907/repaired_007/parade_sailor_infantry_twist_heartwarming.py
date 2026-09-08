#!/usr/bin/env python3
"""
A small storyworld about a sailor, an infantry child, and a parade with a
heartwarming twist: the quiet flag bearer is leading a welcome parade for a
returning parent.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
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
class ParadePlan:
    key: str
    object_name: str
    opening: tuple[str, str]
    trouble: tuple[str, str]
    teamwork: tuple[str, str]
    twist: tuple[str, str]
    ending: tuple[str, str]


PLANS = (
    ParadePlan(
        "flag_ribbon",
        "blue flag",
        (
            "In the harbor square, {sailor} polished a little drum while {infantry} carried a blue flag.",
            "They were preparing a bright parade for the whole town.",
        ),
        (
            "A gust tugged the flag ribbon loose, and the flag drooped beside the marching path.",
            '"The parade will look empty," said {infantry}. "We still have time," said {sailor}.',
        ),
        (
            "{sailor} held the flagpole steady while {infantry} tied the ribbon in a careful double knot.",
            '"You hold the top," said {sailor}. "You guide the knot," said {infantry}.',
        ),
        (
            "Then the harbor bell rang, and {infantry} saw a familiar sailor stepping from the ferry.",
            "The parade was not for a grand captain at all. It was a welcome home for {infantry}'s mother.",
        ),
        (
            "The blue flag waved as the infantry child ran into the sailor's open arms.",
            "The drumbeat softened, and the whole parade smiled at the warmest surprise.",
        ),
    ),
    ParadePlan(
        "drumstrap",
        "red drum",
        (
            "Near the pier, {sailor} tuned a red drum while {infantry} straightened the parade line.",
            "Every marcher was ready to make the harbor ring.",
        ),
        (
            "The drumstrap snapped, and the drum rolled under a bench just before the parade began.",
            '"We need a new strap," said {sailor}. "And a calm plan," said {infantry}.',
        ),
        (
            "{infantry} fetched a sturdy scarf while {sailor} threaded it through the drum hooks.",
            '"Pull gently," said {infantry}. "Now it is safe," said {sailor}.',
        ),
        (
            "A small boat glided in, carrying the sailor's little brother after his first long voyage.",
            "The marching band had gathered to welcome him, though he thought the parade was for someone else.",
        ),
        (
            "The repaired drum boomed, and the sailor and infantry child led the happy welcome together.",
            "The surprise made the new voyager laugh, and the harbor shone with waving hands.",
        ),
    ),
    ParadePlan(
        "paper_star",
        "gold paper star",
        (
            "At the town pier, {sailor} hung bunting while {infantry} carried a gold paper star.",
            "The parade would wind from the lighthouse to the market gate.",
        ),
        (
            "Rain softened the star and folded one bright point against the pole.",
            '"The star is tired," said {infantry}. "Then we will help it shine," said {sailor}.',
        ),
        (
            "{sailor} sheltered the paper with a sailcloth while {infantry} added a dry cardboard point.",
            '"A small repair can hold a big hope," said {sailor}. "Let us try," said {infantry}.',
        ),
        (
            "When the clouds opened, a quiet veteran sailor appeared at the lighthouse steps.",
            "The parade was a secret thank-you for the sailor who had taught the town's children to steer.",
        ),
        (
            "The patched star led the parade, and the honored sailor touched its bright new point.",
            "Everyone learned that a thing repaired with care can shine more sweetly than a perfect thing.",
        ),
    ),
)


@dataclass
class StoryParams:
    place: str
    sailor_name: str
    infantry_name: str
    sailor_gender: str = "woman"
    infantry_gender: str = "child"
    seed: Optional[int] = None


PLACES = {
    "harbor_square": "the harbor square",
    "lighthouse_road": "the lighthouse road",
    "market_pier": "the market pier",
}

SAILOR_NAMES = ["Mara", "Finn", "Nell", "Owen"]
INFANTRY_NAMES = ["Iris", "Leo", "Mina", "Sam"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    sailor = args.sailor or rng.choice(SAILOR_NAMES)
    infantry = args.infantry or rng.choice([n for n in INFANTRY_NAMES if n != sailor])
    return StoryParams(
        place=place,
        sailor_name=sailor,
        infantry_name=infantry,
        sailor_gender=args.sailor_gender or "woman",
        infantry_gender=args.infantry_gender or "child",
    )


def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown parade place: {params.place}.")
    if not params.sailor_name.strip() or not params.infantry_name.strip():
        raise StoryError("The sailor and infantry names must not be empty.")
    if params.sailor_name == params.infantry_name:
        raise StoryError("The sailor and infantry child need different names.")

    rng = random.Random(params.seed if params.seed is not None else 0)
    plan = PLANS[rng.randrange(len(PLANS))]
    sailor = Entity(
        id="sailor",
        kind="character",
        label=params.sailor_name,
        role="sailor",
        meters={"care": 1.0, "steady_hands": 1.0},
        memes={"hope": 1.0, "warmth": 1.0},
    )
    infantry = Entity(
        id="infantry",
        kind="character",
        label=params.infantry_name,
        role="infantry",
        meters={"courage": 1.0, "helped": 0.0},
        memes={"worry": 1.0, "pride": 0.0},
    )
    parade = Entity(
        id="parade",
        kind="event",
        label="the welcome parade",
        role="parade",
        meters={"ready": 0.0, "heart": 0.0},
        memes={},
    )
    world = World(place=PLACES[params.place])
    world.add(sailor)
    world.add(infantry)
    world.add(parade)

    values = {
        "sailor": sailor.label,
        "infantry": infantry.label,
    }
    for line in plan.opening:
        world.say(line.format(**values))
    world.para()

    sailor.meters["steady_hands"] += 1.0
    infantry.memes["worry"] += 1.0
    for line in plan.trouble:
        world.say(line.format(**values))
    world.para()

    infantry.meters["helped"] = 1.0
    sailor.meters["care"] += 1.0
    parade.meters["ready"] = 1.0
    for line in plan.teamwork:
        world.say(line.format(**values))
    world.para()

    parade.meters["heart"] = 1.0
    sailor.memes["warmth"] += 1.0
    infantry.memes["worry"] = 0.0
    infantry.memes["pride"] = 1.0
    for line in plan.twist:
        world.say(line.format(**values))
    world.para()

    for line in plan.ending:
        world.say(line.format(**values))

    world.facts.update(
        plan=plan,
        sailor=sailor,
        infantry=infantry,
        parade=parade,
        place=world.place,
        object_name=plan.object_name,
        twist=plan.twist[1].format(**values),
        result=plan.ending[0].format(**values),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a heartwarming child-facing story containing a parade, a sailor, and an infantry child.",
        f"Tell how {f['sailor'].label} and {f['infantry'].label} repair a {f['object_name']} before a parade.",
        "Include a gentle twist that reveals the parade is a loving welcome for someone special.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What went wrong before the parade?",
            answer=f"The {f['object_name']} was damaged just before the parade, so the sailor and infantry child had to repair it together.",
        ),
        QAItem(
            question="How did the sailor and infantry child help each other?",
            answer=f"They worked as a team: the sailor used steady hands and the infantry child helped with the careful repair.",
        ),
        QAItem(
            question="What was the heartwarming twist?",
            answer=f"The twist was that {f['twist']}",
        ),
        QAItem(
            question="What showed that their plan worked?",
            answer=f"{f['result']} This showed that the parade was ready and full of care.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a sailor do?",
            answer="A sailor works on or around boats and knows how to travel safely on water.",
        ),
        QAItem(
            question="What is an infantry member?",
            answer="An infantry member is a person trained to travel and work on foot as part of a group.",
        ),
        QAItem(
            question="Why do people have parades?",
            answer="People have parades to celebrate, welcome someone, remember something important, or share joy with a community.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:9} ({entity.role:8}) "
            f"meters={meters} memes={memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
ready(parade) :- repaired(object), parade(parade).
welcome(parade) :- ready(parade), heart(parade).
happy(infantry) :- welcome(parade), infantry(infantry).
repaired(object) :- sailor(sailor), infantry(infantry), care(sailor), courage(infantry).
heart(parade) :- twist(parade).
#show welcome/1.
#show happy/1.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("sailor", "sailor"),
            asp.fact("infantry", "infantry"),
            asp.fact("parade", "parade"),
            asp.fact("object", "flag"),
            asp.fact("care", "sailor"),
            asp.fact("courage", "infantry"),
            asp.fact("repaired", "flag"),
            asp.fact("twist", "parade"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(asp.atoms(model, "welcome"))


def asp_verify() -> int:
    import asp

    try:
        model = asp.one_model(asp_program())
        welcome = asp.atoms(model, "welcome")
        if ("parade",) not in welcome:
            print("ASP parity failed: parade was not welcomed.")
            return 1
        sample = generate(
            StoryParams(
                place="harbor_square",
                sailor_name="Mara",
                infantry_name="Iris",
                seed=3,
            )
        )
        if "parade" not in sample.story.lower() or "sailor" not in sample.story.lower():
            print("Generation smoke test failed.")
            return 1
    except Exception as exc:
        print(f"Verification failed: {exc}")
        return 1
    print("OK: ASP and Python smoke tests passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a heartwarming sailor and infantry parade story."
    )
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--sailor")
    parser.add_argument("--infantry")
    parser.add_argument("--sailor-gender", choices=["woman", "man"])
    parser.add_argument("--infantry-gender", choices=["child", "girl", "boy"])
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
        print()
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
        print(asp_valid_combos())
        return

    if args.n < 1:
        raise SystemExit("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams(
                place=place,
                sailor_name=SAILOR_NAMES[i % len(SAILOR_NAMES)],
                infantry_name=INFANTRY_NAMES[(i + 1) % len(INFANTRY_NAMES)],
                seed=base_seed + i,
            )
            for i, place in enumerate(PLACES)
        ]
    else:
        params_list = []
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            params_list.append(params)

    samples = [generate(params) for params in params_list]

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
