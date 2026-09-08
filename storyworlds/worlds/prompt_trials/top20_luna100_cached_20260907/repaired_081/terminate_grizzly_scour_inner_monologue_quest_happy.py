#!/usr/bin/env python3
"""
Story world: a cheerful superhero quest to scour a grizzly's den before danger
can terminate the town's honey festival.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str = "Luna"
    helper_name: str = "Pip"
    town: str = "Brightbell"
    grizzly_name: str = "Bruno"
    quest: str = "honey festival"
    telling_mode: str = "inner monologue"
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


HERO_NAMES = ["Luna", "Nova", "Mira", "Sol", "Zara"]
HELPER_NAMES = ["Pip", "Ollie", "Bee", "Tavi", "Rin"]
TOWNS = ["Brightbell", "Sunpatch", "Moonmeadow", "Clover Hill"]
QUESTS = ["honey festival", "lantern parade", "garden fair", "berry picnic"]
TELLING_MODES = ["inner monologue", "bold opening", "mystery opening", "quiet opening"]

ASP_RULES = r"""
hero(H) :- hero_name(H).
grizzly(G) :- grizzly_name(G).
quest(Q) :- quest_name(Q).
scoured(D) :- den_state(D, clean).
safe(G) :- grizzly_name(G), fed(G), calm(G).
happy_ending :- scoured(den), safe(bruno), festival_saved.
"""


def asp_facts() -> str:
    import asp

    return "\n".join([
        asp.fact("hero_name", "luna"),
        asp.fact("grizzly_name", "bruno"),
        asp.fact("quest_name", "honey_festival"),
        asp.fact("den_state", "den", "clean"),
        asp.fact("fed", "bruno"),
        asp.fact("calm", "bruno"),
        asp.fact("festival_saved"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program(
        "#show scoured/1.\n#show safe/1.\n#show happy_ending/0."
    ))
    got = {
        (sym.name, tuple(
            a.string if a.type == a.type.String
            else a.number if a.type == a.type.Number
            else a.name
            for a in sym.arguments
        ))
        for sym in model
    }
    want = {
        ("scoured", ("den",)),
        ("safe", ("bruno",)),
        ("happy_ending", ()),
    }
    if got == want:
        print("OK: ASP and Python parity looks good.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("ASP:", sorted(got))
    print("PY :", sorted(want))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A superhero quest about Luna, a grizzly, and a happy ending."
    )
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--town", choices=TOWNS)
    parser.add_argument("--grizzly", default="Bruno")
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
    hero = args.name or rng.choice(HERO_NAMES)
    helpers = [name for name in HELPER_NAMES if name != hero]
    helper = args.helper or rng.choice(helpers)
    if hero == helper:
        raise StoryError("The superhero and helper must be different characters.")
    grizzly = args.grizzly
    if not grizzly or not grizzly.strip():
        raise StoryError("The grizzly needs a name.")
    return StoryParams(
        hero_name=hero,
        helper_name=helper,
        town=args.town or rng.choice(TOWNS),
        grizzly_name=grizzly,
        quest=rng.choice(QUESTS),
        telling_mode=rng.choice(TELLING_MODES),
    )


def generate(params: StoryParams) -> StorySample:
    if params.hero_name == params.helper_name:
        raise StoryError("The superhero and helper must be different characters.")
    if not params.grizzly_name.strip():
        raise StoryError("The grizzly needs a name.")

    rng = random.Random(
        params.seed
        if params.seed is not None
        else f"{params.hero_name}:{params.helper_name}:{params.town}:{params.grizzly_name}"
    )
    world = World()

    hero = world.add(Entity(
        "hero", "superhero", params.hero_name,
        meters={"bravery": 1.0, "energy": 1.0},
        memes={"worry": 0.0, "hope": 1.0},
    ))
    helper = world.add(Entity(
        "helper", "helper", params.helper_name,
        meters={"care": 1.0},
        memes={"trust": 1.0},
    ))
    grizzly = world.add(Entity(
        "grizzly", "grizzly", params.grizzly_name,
        meters={"hunger": 1.0, "calm": 0.0},
        memes={"loneliness": 1.0},
    ))
    den = world.add(Entity(
        "den", "place", "the grizzly's den",
        meters={"clutter": 1.0, "safety": 0.0},
        memes={"welcome": 0.0},
    ))

    openings = {
        "inner monologue": (
            f"Luna stood beneath the bright flags of {params.town} and thought, "
            f"I can protect the {params.quest}, but I must understand the danger first."
        ),
        "bold opening": (
            f"When a grizzly growled near {params.town}, {params.hero_name} "
            f"leaped into action as the town's newest superhero."
        ),
        "mystery opening": (
            f"Every jar of honey rattled in {params.town}, though no one knew why "
            f"the grizzly had come so close to the {params.quest}."
        ),
        "quiet opening": (
            f"The morning of the {params.quest} was soft and golden in {params.town}, "
            f"until {params.hero_name} noticed pawprints beside the road."
        ),
    }
    world.say(openings[params.telling_mode])
    world.say(
        f"The grizzly had been drawn from the hills by a sweet smell and a den "
        f"cluttered with torn sacks, sticky wrappers, and old festival ribbons."
    )
    world.say(
        f"{params.hero_name} wanted to terminate the danger quickly, but the grizzly "
        f"looked frightened rather than fierce."
    )
    hero.meters["bravery"] += 1.0
    hero.memes["worry"] += 1.0
    grizzly.meters["hunger"] += 1.0
    den.meters["clutter"] += 1.0

    world.say(
        f"“Should we chase {params.grizzly_name} away?” {params.hero_name} asked."
    )
    world.say(
        f"“Let us scour the den for the cause first,” {params.helper_name} replied. "
        f"“A hungry animal may need help, not a battle.”"
    )
    world.say(
        f"Those words changed {params.hero_name}'s plan. The superhero lowered "
        f"their bright shield and followed the pawprints instead of rushing forward."
    )
    world.say(
        f"Inside the den, {params.hero_name} and {params.helper_name} found a leaking "
        f"honey tin, a sharp metal lid, and ribbons wrapped around the sleeping place."
    )
    world.say(
        f"The sharp lid had cut {params.grizzly_name}'s paw, while the sweet tin "
        f"had made the grizzly hungry and restless."
    )

    den.meters["clutter"] = 0.0
    den.meters["safety"] = 1.0
    den.memes["welcome"] = 1.0
    grizzly.meters["hunger"] = 0.0
    grizzly.meters["calm"] = 1.0
    grizzly.memes["loneliness"] = 0.0
    hero.meters["energy"] += 0.5
    hero.memes["worry"] = 0.0
    hero.memes["hope"] += 1.0

    world.say(
        f"Together they scoured the den. They removed the sharp lid, gathered the "
        f"ribbons, sealed the honey tin, and placed clean water beside the entrance."
    )
    world.say(
        f"{params.hero_name} kept a safe distance while {params.helper_name} set "
        f"berries on a flat stone, so the grizzly could choose its own way home."
    )
    world.say(
        f"“I thought being a superhero meant stopping every threat,” "
        f"{params.hero_name} admitted."
    )
    world.say(
        f"“Sometimes a hero stops danger by discovering what is hurting someone,” "
        f"{params.helper_name} said."
    )
    world.say(
        f"{params.grizzly_name} sniffed the clean den, ate the berries, and gave a "
        f"gentle huff. Then the grizzly lumbered back toward the quiet hills."
    )
    world.say(
        f"The {params.quest} began safely, and {params.hero_name} returned to "
        f"{params.town} with a happy heart and a new kind of superpower: carefulness."
    )
    world.say(
        f"That evening, the grizzly watched the lanterns from far away while Luna "
        f"shared one honey cake with {params.helper_name}; the danger was over, "
        f"the den was safe, and everyone had a reason to smile."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        grizzly=grizzly,
        den=den,
        den_scoured=True,
        grizzly_safe=True,
        festival_saved=True,
        lesson="careful heroes discover causes before they act",
    )

    prompts = [
        f"Write a superhero quest about {params.hero_name} protecting the {params.quest} in {params.town}.",
        f"Include a grizzly named {params.grizzly_name}, a den that must be scoured, and a peaceful solution.",
        "Use inner monologue, a brief dialogue exchange, and a happy ending showing what changed.",
    ]
    story_qa = [
        QAItem(
            "Why did the grizzly come near the town?",
            f"The grizzly came near {params.town} because a leaking honey tin made the animal hungry and restless, while the den was cluttered and unsafe.",
        ),
        QAItem(
            f"What did {params.hero_name} and {params.helper_name} discover?",
            f"They discovered a sharp metal lid, a leaking honey tin, and ribbons tangled inside {params.grizzly_name}'s den.",
        ),
        QAItem(
            "How did the heroes solve the problem?",
            f"They scoured the den, removed the sharp lid and ribbons, sealed the honey tin, and left clean water and berries at a safe distance.",
        ),
        QAItem(
            f"What did {params.hero_name} learn?",
            f"{params.hero_name} learned that a careful hero discovers what is causing danger before trying to stop it.",
        ),
        QAItem(
            "How did the story end happily?",
            f"The grizzly returned to the hills, the den became safe, and the town enjoyed its festival without danger.",
        ),
    ]
    world_qa = [
        QAItem(
            "What is a grizzly?",
            "A grizzly is a large brown bear that lives in parts of North America.",
        ),
        QAItem(
            "What does scour mean?",
            "To scour means to search or clean something thoroughly.",
        ),
        QAItem(
            "What makes a superhero's help safe?",
            "A superhero's help is safe when it protects people and animals while respecting distance, evidence, and the needs of others.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for key, entity in sample.world.entities.items():
            print(f"{key}: {entity.label} meters={entity.meters} memes={entity.memes}")
    if qa:
        print("\n== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show scoured/1.\n#show safe/1.\n#show happy_ending/0."))
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for town in TOWNS:
            params = StoryParams(
                hero_name=HERO_NAMES[0],
                helper_name=HELPER_NAMES[0],
                town=town,
                grizzly_name="Bruno",
                quest=QUESTS[0],
                telling_mode="inner monologue",
                seed=base_seed + len(samples),
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(1, args.n) and index < max(50, args.n * 20):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

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
