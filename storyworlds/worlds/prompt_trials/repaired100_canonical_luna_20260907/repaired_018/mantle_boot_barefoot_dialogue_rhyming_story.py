#!/usr/bin/env python3
"""
A small rhyming storyworld about a mantle, a boot, and a barefoot walk.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = next(
    parent for parent in Path(__file__).resolve().parents if (parent / "results.py").is_file()
)
sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


HERO_NAMES = ["Luna", "Mira", "Poppy", "Nell", "Toby", "Ivy"]
HELPER_NAMES = ["Aunt Bea", "Grandpa Sol", "Milo", "Rae", "Uncle Finn"]
MANTLE_COLORS = ["red", "golden", "blue", "green", "purple"]
PLACES = ["the cottage porch", "the moonlit garden", "the little village lane", "the warm hall"]
PURPOSES = [
    "carry a lantern to the sleepy gate",
    "bring a blanket to the chilly lamb",
    "deliver a bell to the evening parade",
    "fetch a basket of apples from the old shed",
]
MATERIALS = ["soft wool", "striped cloth", "warm velvet", "thick woven yarn"]

ASP_RULES = r"""
usable_mantle(C) :- mantle_color(C).
safe_boot(S) :- boot_size(S).
barefoot_problem :- has_mantle, has_boot, needs_walk.
dialogue_story :- has_dialogue.
rhyming_story :- has_rhyme.
ready_to_walk :- usable_mantle(C), safe_boot(S), repaired_boot.
solved :- ready_to_walk, dialogue_story, rhyming_story.
#show usable_mantle/1.
#show safe_boot/1.
#show barefoot_problem/0.
#show dialogue_story/0.
#show rhyming_story/0.
#show ready_to_walk/0.
#show solved/0.
"""


@dataclass
class StoryParams:
    hero: str
    helper: str
    mantle_color: str
    boot_size: str
    place: str
    purpose: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rhyming mantle, boot, and barefoot storyworld.")
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--mantle-color", choices=MANTLE_COLORS)
    parser.add_argument("--boot-size", choices=["small", "medium", "large"])
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--purpose", choices=PURPOSES)
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
        hero=args.hero or rng.choice(HERO_NAMES),
        helper=args.helper or rng.choice(HELPER_NAMES),
        mantle_color=args.mantle_color or rng.choice(MANTLE_COLORS),
        boot_size=args.boot_size or rng.choice(["small", "medium", "large"]),
        place=args.place or rng.choice(PLACES),
        purpose=args.purpose or rng.choice(PURPOSES),
    )


def build_world(params: StoryParams) -> World:
    world = World(params)
    world.add(Entity("hero", "character", params.hero, memes={"hope": 1.0}))
    world.add(Entity("helper", "character", params.helper, memes={"care": 1.0}))
    world.add(Entity("mantle", "garment", f"{params.mantle_color} mantle", memes={"warmth": 1.0}))
    world.add(Entity("boot", "clothing", f"{params.boot_size} boot", meters={"fit": 0.0}))
    world.add(Entity("ground", "place", params.place, meters={"cold": 1.0}))
    return world


def generate_story(world: World) -> None:
    p = world.params
    hero = world.entities["hero"]
    helper = world.entities["helper"]
    boot = world.entities["boot"]

    world.say(
        f"{p.hero} wore a {p.mantle_color} mantle, bright in the night, "
        f"and set out from {p.place} in moon-silver light."
    )
    world.say(
        f"Their task was to {p.purpose}; the breeze hummed low, "
        f"but one boot slipped off with a soft tiptoe."
    )

    world.para()
    world.say(
        f"'Oh dear,' said {p.hero}, 'my boot has fled! "
        f"I am barefoot instead of snug in bed!'"
    )
    world.say(
        f"'{p.hero},' said {p.helper}, 'do not dash or leap. "
        f"We will find that boot before the moon falls asleep.'"
    )
    world.say(
        f"They searched by the step and beneath the old chair, "
        f"while the {p.hero}'s bare foot felt cool evening air."
    )
    world.facts["trouble"] = "the boot slipped off and left the hero barefoot"
    world.facts["dialogue"] = True
    hero.memes["worry"] = 1.0
    boot.meters["fit"] = 0.0

    world.para()
    world.say(
        f"'Look!' cried {p.hero}. 'A trail by the gate! "
        f"Three moon-drops of mud show the boot's tiny route.'"
    )
    world.say(
        f"'{p.hero},' said {p.helper}, 'your mantle's red glow "
        f"shines on the place where the lost boot must go.'"
    )
    world.say(
        f"Behind a round stone, tucked under a leaf, "
        f"sat the {p.boot_size} boot, a shy little thief."
    )
    world.say(
        f"{p.hero} laughed, 'Boot, you may hide, but you cannot stay. "
        f"Come warm my barefoot and walk the right way!'"
    )
    world.facts["clue"] = "moonlit mud drops led to the boot behind a stone"
    world.facts["actual_cause"] = "the boot had slipped behind a stone"
    hero.memes["curious"] = 1.0

    world.para()
    world.say(
        f"{p.helper} brushed off the dirt with a careful hand, "
        f"and {p.hero} put the boot on firm ground to stand."
    )
    world.say(
        f"The mantle wrapped warmly; the boot fit just right, "
        f"so barefoot toes waved goodbye to the night."
    )
    world.say(
        f"Together they went to {p.purpose}, "
        f"with a steady small step and a cheerful tune."
    )
    world.say(
        f"The lantern shone bright at the sleepy gate, "
        f"and the moon sang, 'You made it—not early, not late!'"
    )
    world.say(
        f"At home, the mantle hung softly beside the door, "
        f"and the boot stayed ready on the warm wooden floor."
    )
    world.facts.update(
        {
            "solution": "the helper followed the mud trail and found the boot",
            "result": "the hero put the boot back on and completed the errand",
            "ending": "the mantle hung beside the boot while the moon shone outside",
            "settled": True,
        }
    )
    hero.memes["worry"] = 0.0
    hero.memes["joy"] = 2.0
    helper.memes["joy"] = 1.0
    boot.meters["fit"] = 1.0
    world.entities["ground"].meters["cold"] = 0.0


def generate(params: StoryParams) -> StorySample:
    if params.mantle_color not in MANTLE_COLORS:
        raise StoryError(f"Unknown mantle color: {params.mantle_color}")
    if params.boot_size not in {"small", "medium", "large"}:
        raise StoryError(f"Unknown boot size: {params.boot_size}")
    world = build_world(params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a rhyming story about {params.hero}, a mantle, and a boot.",
            f"Include dialogue as {params.hero} solves a barefoot problem with {params.helper}.",
            f"Tell a child-friendly tale set in {params.place}, ending with the boot found.",
        ],
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    f = world.facts
    return [
        QAItem(
            f"Why did {p.hero} become barefoot?",
            f"{p.hero} became barefoot because the {p.boot_size} boot slipped off while they were leaving {p.place}.",
        ),
        QAItem(
            f"How did {p.hero} and {p.helper} find the boot?",
            f"They followed three moon-drops of mud, which led behind a round stone where the boot was hiding.",
        ),
        QAItem(
            f"How was the problem solved?",
            f"{p.helper} brushed off the boot, and {p.hero} put it back on. Then they could finish their task to {p.purpose}.",
        ),
        QAItem(
            f"What showed that everything was all right at the end?",
            f"The mantle hung beside the boot, the boot stayed ready on the warm wooden floor, and the moon shone outside.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a mantle?", "A mantle is a loose covering or cloak worn over clothing to keep someone warm."),
        QAItem("What does barefoot mean?", "Barefoot means having no shoes or boots on the feet."),
        QAItem("Why can dialogue help in a story?", "Dialogue lets characters share clues, feelings, and plans so their words can change what happens."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:8} ({entity.kind:10}) {entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    lines = [asp.fact("has_mantle"), asp.fact("has_boot"), asp.fact("needs_walk")]
    for color in MANTLE_COLORS:
        lines.append(asp.fact("mantle_color", color))
    for size in ["small", "medium", "large"]:
        lines.append(asp.fact("boot_size", size))
    lines.extend([asp.fact("repaired_boot"), asp.fact("has_dialogue"), asp.fact("has_rhyme")])
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    required = {
        "barefoot_problem",
        "dialogue_story",
        "rhyming_story",
        "ready_to_walk",
        "solved",
    }
    shown = {sym.name for sym in model if sym.name in required}
    if not required.issubset(shown):
        print("Mismatch between ASP rules and Python story features.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.story or "barefoot" not in sample.story or "boot" not in sample.story:
            print("Generated story verification failed.")
            return 1
    print("OK: ASP parity and generated-story checks passed.")
    return 0


def emit(sample: StorySample, *, trace: bool, qa: bool, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for prompt in sample.prompts:
            print(f"P: {prompt}")
        for item in sample.story_qa + sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams("Luna", "Aunt Bea", "red", "small", "the cottage porch", "carry a lantern to the sleepy gate"),
    StoryParams("Mira", "Grandpa Sol", "golden", "medium", "the moonlit garden", "bring a blanket to the chilly lamb"),
    StoryParams("Poppy", "Rae", "blue", "large", "the little village lane", "deliver a bell to the evening parade"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import asp
            model = asp.one_model(asp_program())
            for name in ["barefoot_problem", "dialogue_story", "rhyming_story", "ready_to_walk", "solved"]:
                print(f"{name}={len(asp.atoms(model, name))}")
        except Exception as exc:
            raise SystemExit(f"ASP unavailable: {exc}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(max(0, args.n)):
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
        header = ""
        if args.all:
            header = f"### {sample.params.hero} and the lost boot"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
