#!/usr/bin/env python3
"""A child-friendly space adventure about candid words and a surprising curtain."""

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


SETTINGS = {
    "moon": "the Moon's silver orbit",
    "nebula": "the violet nebula",
    "asteroid": "the gentle asteroid belt",
}
HEROES = ("Luna", "Nova", "Mira", "Orion")
BUDDIES = ("Pip", "Comet", "Zig", "Tess")
CURTAINS = ("the crimson curtain", "the starry curtain", "the golden curtain")
REVEALS = (
    ("a tiny greenhouse", "a row of moon beans waved in zero gravity"),
    ("a lost repair robot", "its round eyes blinked beside a box of silver tools"),
    ("a sleeping comet kitten", "its tail curled around a cushion of stardust"),
    ("a secret telescope", "its lens opened and painted a new star on the ceiling"),
)


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    setting: str = SETTINGS["moon"]
    hero: str = "Luna"
    buddy: str = "Pip"
    curtain: str = CURTAINS[0]
    seed: Optional[int] = None


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Space adventure with a surprising curtain.")
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--buddy", choices=BUDDIES)
    parser.add_argument("--curtain", choices=CURTAINS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting_key = args.setting or rng.choice(tuple(SETTINGS))
    hero = args.hero or rng.choice(HEROES)
    buddy_choices = [name for name in BUDDIES if name != hero]
    buddy = args.buddy or rng.choice(buddy_choices)
    if buddy == hero:
        raise StoryError("The hero and buddy must have different names.")
    return StoryParams(
        setting=SETTINGS[setting_key],
        hero=hero,
        buddy=buddy,
        curtain=args.curtain or rng.choice(CURTAINS),
    )


def tell(params: StoryParams) -> World:
    if params.hero == params.buddy:
        raise StoryError("The hero and buddy must be different characters.")
    reveal, image = REVEALS[(params.seed or 0) % len(REVEALS)]
    world = World(params)
    hero = world.add(Entity(
        "hero", "character", params.hero, "hero",
        meters={"fuel": 1.0, "courage": 1.0},
        memes={"curiosity": 1.0, "trust": 1.0},
        traits=["careful pilot"],
    ))
    buddy = world.add(Entity(
        "buddy", "character", params.buddy, "buddy",
        meters={"fuel": 1.0, "courage": 1.0},
        memes={"curiosity": 1.0, "trust": 1.0},
        traits=["honest helper"],
    ))
    curtain = world.add(Entity(
        "curtain", "object", params.curtain, "curtain",
        meters={"tension": 1.0},
        memes={"mystery": 2.0},
        traits=["stitched with tiny stars"],
    ))

    world.say(f"On a quiet flight through {params.setting}, {params.hero} and {params.buddy} steered their little starship.")
    world.say(f"A {params.curtain} covered a hatch at the back of the ship, and a soft humming sound came from behind it.")
    world.say(f"“I candidly admit I am curious,” said {params.hero}. “Should we open it?”")
    world.say(f"“We should first check the ship map,” replied {params.buddy}. “A surprise is best when everyone is safe.”")

    world.para()
    world.say("They studied the blinking map. The hatch was not marked as dangerous, but its handle was loose and the ship was passing through a patch of glittering space dust.")
    world.say(f"{params.hero} held the ship steady while {params.buddy} clipped a safety cord to the {params.curtain}.")
    world.say(f"“Candid question,” said {params.buddy}. “What if the humming is a tiny engine?”")
    world.say(f"“Then we will not pull hard,” said {params.hero}. “We will listen, loosen the catch, and move slowly.”")
    hero.meters["courage"] += 1.0
    buddy.meters["courage"] += 1.0

    world.para()
    world.say(f"Together they counted three stars and lifted the {params.curtain} one careful inch at a time.")
    world.say(f"The humming stopped. Then the hatch opened with a gentle puff, revealing {reveal}.")
    world.say(f"It was a wonderful surprise: {image}.")
    world.say(f"“I thought we would find a broken machine,” said {params.hero}.")
    world.say(f"{params.buddy} laughed. “Your candid guess was wrong, but your careful plan was exactly right.”")
    curtain.meters["tension"] = 0.0
    curtain.memes["mystery"] = 0.0
    hero.memes["trust"] += 1.0
    buddy.memes["trust"] += 1.0

    world.para()
    world.say(f"They secured the hatch, shared the discovery with mission control, and gave the hidden {reveal} a safe place on the ship.")
    world.say(f"As the starship sailed onward, the {params.curtain} became a cheerful doorway instead of a worrying mystery.")
    world.say(f"{params.hero} and {params.buddy} smiled beneath the stars, glad that honest words and careful teamwork had made room for a surprise.")

    world.facts.update(
        hero=hero,
        buddy=buddy,
        curtain=curtain,
        setting=params.setting,
        reveal=reveal,
        image=image,
        safe=True,
        candid=True,
        surprise=True,
        dialogue=True,
        teamwork=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"].label
    buddy = f["buddy"].label
    curtain = f["curtain"].label
    return [
        f"Write a child-friendly Space Adventure about {hero} and {buddy} investigating {curtain}.",
        f"Include candid dialogue, a careful safety plan, and a surprise behind {curtain}.",
        "Show how listening and teamwork change a mysterious space problem into a joyful discovery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].label
    buddy = f["buddy"].label
    curtain = f["curtain"].label
    reveal = f["reveal"]
    return [
        QAItem(
            question=f"Why did {hero} and {buddy} wait before opening the {curtain}?",
            answer=f"They checked the ship map and attached a safety cord because the ship was moving through glittering space dust and the hatch handle was loose.",
        ),
        QAItem(
            question=f"What did {hero} and {buddy} find behind the {curtain}?",
            answer=f"They found {reveal}, and the discovery became a happy surprise instead of a dangerous mystery.",
        ),
        QAItem(
            question=f"How did the friends use candid words?",
            answer=f"{hero} honestly admitted being curious, and {buddy} openly asked what might be humming behind the curtain. Their honest words helped them make a careful plan.",
        ),
        QAItem(
            question="How did their plan change the adventure?",
            answer=f"{hero} held the ship steady while {buddy} secured the curtain, so they could open the hatch slowly and discover {reveal} safely.",
        ),
        QAItem(
            question="What showed that the problem was solved?",
            answer=f"They secured the hatch and gave the hidden discovery a safe place on the ship, while the curtain became a cheerful doorway.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a curtain?",
            answer="A curtain is a piece of cloth that can cover a window, doorway, or opening.",
        ),
        QAItem(
            question="What does candid mean?",
            answer="Candid means honest and open about what someone thinks or feels.",
        ),
        QAItem(
            question="Why is teamwork useful in space?",
            answer="Teamwork helps space travelers share observations, check safety, and solve problems together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.extend(["", "== story qa =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.extend(["", "== world qa =="])
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: meters={entity.meters} memes={entity.memes} traits={entity.traits}"
        )
    lines.append(f"facts: {sorted(world.facts)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid_setting/1.
#show valid_curtain/1.
valid_setting(moon).
valid_setting(nebula).
valid_setting(asteroid).
valid_curtain(crimson).
valid_curtain(starry).
valid_curtain(golden).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", key) for key in SETTINGS]
    lines += [
        asp.fact("curtain", "crimson"),
        asp.fact("curtain", "starry"),
        asp.fact("curtain", "golden"),
    ]
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program("#show valid_setting/1.\n#show valid_curtain/1."))
    except ImportError:
        print("ASP verification unavailable: clingo is not installed.")
        return 0
    settings = sorted(asp.atoms(model, "valid_setting"))
    curtains = sorted(asp.atoms(model, "valid_curtain"))
    expected_settings = sorted((key,) for key in SETTINGS)
    expected_curtains = sorted((key,) for key in ("crimson", "starry", "golden"))
    if settings != expected_settings or curtains != expected_curtains:
        print("MISMATCH: ASP registry facts differ from Python registries.")
        return 1
    for seed in range(4):
        sample = generate(StoryParams(seed=seed))
        if not sample.story or "surprise" not in sample.story.lower():
            print("MISMATCH: generated story failed the surprise check.")
            return 1
    print("OK: ASP/Python parity and generated-story checks passed.")
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


CURATED = [
    StoryParams(setting=SETTINGS["moon"], hero="Luna", buddy="Pip", curtain=CURTAINS[0], seed=0),
    StoryParams(setting=SETTINGS["nebula"], hero="Nova", buddy="Comet", curtain=CURTAINS[1], seed=1),
    StoryParams(setting=SETTINGS["asteroid"], hero="Mira", buddy="Zig", curtain=CURTAINS[2], seed=2),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_setting/1.\n#show valid_curtain/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("Valid settings:", ", ".join(SETTINGS))
        print("Valid curtains: crimson, starry, golden")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if args.all:
            header = f"### {sample.params.hero} and {sample.params.buddy} in {sample.params.setting}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
