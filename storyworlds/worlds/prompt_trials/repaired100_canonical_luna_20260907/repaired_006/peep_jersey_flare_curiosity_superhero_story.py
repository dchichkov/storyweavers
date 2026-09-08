#!/usr/bin/env python3
"""
A gentle superhero story about Peep, a bright jersey, and a puzzling flare.
Curiosity becomes the power that helps a small hero protect the night.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


SETTINGS = (
    "a rooftop above a quiet city",
    "a small park beneath the evening stars",
    "a lighthouse hill beside the dark sea",
    "a cozy neighborhood with glowing windows",
)

HERO_NAMES = (
    ("Luna", "girl"),
    ("Milo", "boy"),
    ("Ari", "child"),
    ("Zoe", "girl"),
)

JERSEYS = (
    "a red jersey with a silver moon",
    "a blue jersey with a golden star",
    "a green jersey with a bright comet",
    "a purple jersey with a tiny lightning bolt",
)

FLARES = (
    "a blue flare",
    "a green flare",
    "a golden flare",
    "a pink flare",
)

ENDING_IMAGES = (
    "The flare settled into a friendly star above the rooftops, and Peep gave one proud, sleepy peep.",
    "Luna's jersey glowed softly as the rescued light danced over the park and tucked itself behind the moon.",
    "The lighthouse shone again, while Peep curled beside the warm lantern and watched the sea sparkle.",
    "By bedtime, the neighborhood lights twinkled in a safe row, and curiosity felt like a small brave superpower.",
)


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
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


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Luna"
    hero_type: str = "girl"
    setting: str = SETTINGS[0]
    jersey: str = JERSEYS[0]
    flare: str = FLARES[0]
    ending: str = ENDING_IMAGES[0]


def tell(params: StoryParams) -> World:
    world = World(params.setting)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        label=params.hero_name,
        meters={"courage": 1.0},
        memes={"curiosity": 1.0, "worry": 0.0},
    ))
    peep = world.add(Entity(
        id="peep",
        kind="animal",
        label="Peep",
        meters={"brightness": 0.6},
        memes={"trust": 1.0},
    ))
    jersey = world.add(Entity(
        id="jersey",
        kind="clothing",
        label=params.jersey,
        meters={"visibility": 1.0},
        memes={"heroic": 1.0},
    ))
    flare = world.add(Entity(
        id="flare",
        kind="light",
        label=params.flare,
        meters={"heat": 0.8, "brightness": 1.0},
        memes={"wild": 1.0},
    ))
    world.facts.update(hero=hero, peep=peep, jersey=jersey, flare=flare)

    world.say(
        f"At {params.setting}, {hero.label} wore {params.jersey} and watched over the quiet night."
    )
    world.say(
        f"Beside {hero.label} stood Peep, a tiny bird who could hear even the softest peep in the dark."
    )

    world.para()
    world.say(
        f"Suddenly, {params.flare} streaked over the rooftops and flickered near the old signal tower."
    )
    world.say(
        f'"Should we chase it?" {hero.label} asked. Peep tilted one bright eye and gave a questioning peep.'
    )
    world.say(
        f'"I am curious," {hero.label} said. "But we will look carefully and keep everyone safe."'
    )
    hero.memes["worry"] = 1.0
    world.fired.add("curiosity_guides_choice")

    world.para()
    world.say(
        f"{hero.label} followed the flare's silver trail, while the bright colors of {params.jersey} helped Peep find the path."
    )
    world.say(
        f"At the tower, the flare was not a villain at all. It was a little rescue beacon caught in a nest of windy vines."
    )
    world.say(
        f'"The light is asking for help," {hero.label} whispered. "Peep, can you show me where the vine is loose?"'
    )
    world.say("Peep peeped twice and hopped toward a safe wooden ladder.")
    world.fired.add("secret_understood")

    world.para()
    world.say(
        f"{hero.label} loosened the vine with a small safety hook, and the {params.flare} floated free."
    )
    flare.meters["heat"] = 0.2
    flare.meters["brightness"] = 1.0
    flare.memes["wild"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["relief"] = 1.0
    world.fired.add("flare_rescued")
    world.say(
        f"The rescued flare rose above the tower and sent a warm beam toward the homes below."
    )
    world.say(
        f'"Curiosity helped us notice the trouble," {hero.label} told Peep. "And careful courage helped us fix it."'
    )

    world.para()
    world.say(params.ending)
    return world


ASP_RULES = r"""
curious(hero).
has_peep(hero, peep).
has_jersey(hero, jersey).
flare_needs_help(flare).
safe_choice(hero) :- curious(hero), has_peep(hero, peep), has_jersey(hero, jersey).
rescued(flare) :- flare_needs_help(flare), safe_choice(hero).
heroic(hero) :- rescued(flare).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("curious", "hero"),
        asp.fact("has_peep", "hero", "peep"),
        asp.fact("has_jersey", "hero", "jersey"),
        asp.fact("flare_needs_help", "flare"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program(
        "#show safe_choice/1.\n#show rescued/1.\n#show heroic/1."
    ))
    safe = set(asp.atoms(model, "safe_choice"))
    rescued = set(asp.atoms(model, "rescued"))
    heroic = set(asp.atoms(model, "heroic"))
    if safe == {("hero",)} and rescued == {("flare",)} and heroic == {("hero",)}:
        sample = generate(StoryParams(seed=0))
        if "Peep" in sample.story and "jersey" in sample.story and "flare" in sample.story:
            print("OK: ASP and Python agree on the curious flare rescue.")
            return 0
    print("MISMATCH between ASP and Python.")
    print("safe_choice:", sorted(safe))
    print("rescued:", sorted(rescued))
    print("heroic:", sorted(heroic))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    seed = args.seed if args.seed is not None else 0
    hero_name, hero_type = HERO_NAMES[seed % len(HERO_NAMES)]
    return StoryParams(
        seed=seed,
        hero_name=hero_name,
        hero_type=hero_type,
        setting=rng.choice(SETTINGS),
        jersey=rng.choice(JERSEYS),
        flare=rng.choice(FLARES),
        ending=rng.choice(ENDING_IMAGES),
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    return [
        "Write a gentle superhero story about Peep, a jersey, and a mysterious flare.",
        f"Tell a story in which {hero.label}'s curiosity leads to a safe rescue.",
        "Show how a small hero uses careful courage instead of rushing into danger.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    return [
        QAItem(
            question=f"Who followed the flare with Peep?",
            answer=f"{hero.label} followed the flare with Peep while wearing {world.facts['jersey'].label}.",
        ),
        QAItem(
            question="Why did the hero investigate the flare?",
            answer=f"{hero.label} investigated because curiosity made the hero wonder whether the flare needed help.",
        ),
        QAItem(
            question="What was wrong with the flare?",
            answer="The flare was a rescue beacon caught in a nest of windy vines near the signal tower.",
        ),
        QAItem(
            question="How was the flare rescued?",
            answer=f"{hero.label} used a small safety hook to loosen the vine, and Peep helped show the safe path.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to learn or understand something by asking questions and looking carefully.",
        ),
        QAItem(
            question="What is a flare?",
            answer="A flare is a bright signal light used to attract attention or show that help may be needed.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


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
        description="A curious superhero story about Peep and a flare."
    )
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(
            "#show safe_choice/1.\n#show rescued/1.\n#show heroic/1."
        ))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program(
            "#show safe_choice/1.\n#show rescued/1.\n#show heroic/1."
        ))
        print("safe_choice:", sorted(set(asp.atoms(model, "safe_choice"))))
        print("rescued:", sorted(set(asp.atoms(model, "rescued"))))
        print("heroic:", sorted(set(asp.atoms(model, "heroic"))))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = len(SETTINGS) * len(JERSEYS) * len(FLARES) if args.all else args.n
    samples: list[StorySample] = []

    for index in range(count):
        seed = base_seed + index
        params = resolve_params(
            argparse.Namespace(seed=seed),
            random.Random(seed),
        )
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
