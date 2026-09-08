#!/usr/bin/env python3
"""
A gentle superhero storyworld about a cub-dim power, an embarrassing pee
problem, and a surprising perk discovered through honest teamwork.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    place: str
    affords: set[str] = field(default_factory=lambda: {"hide", "listen", "solve", "shine"})


@dataclass
class StoryParams:
    hero_name: str
    helper_name: str
    villain_name: str
    place: int = 0
    gadget: int = 0
    perk: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    place: str
    problem: str
    clue: str
    solution: str
    surprise: str
    ending: str


SCENARIOS = [
    Scenario(
        "the Moonbeam School",
        "a little pee accident had dampened the cape closet",
        "a silver trail leading from the closet to a humming floor fan",
        "moved the fan, dried the floor, and placed a bright signal mat by the door",
        "the signal mat glowed whenever someone needed a bathroom break",
        "the young heroes flew home beneath a clean, glowing moon",
    ),
    Scenario(
        "the Cloudtop Playground",
        "a pee puddle made the launch slide too slippery",
        "tiny wet stars beneath the slide ladder",
        "blocked the slide, cleaned it together, and marked the nearby restroom with a comet sign",
        "the comet sign also helped younger cubs find the restroom before trouble started",
        "the playground sparkled safely while the capes snapped in the breeze",
    ),
    Scenario(
        "the Sunflower Library",
        "a pee accident had soaked the corner of the hero-map rug",
        "a trail of yellow droplets beside the reading nook",
        "rolled up the rug, cleaned the spot, and made a quiet bathroom signal",
        "the signal became a secret perk that let shy heroes ask for help without feeling embarrassed",
        "the hero-map dried flat beneath a warm stripe of sunlight",
    ),
    Scenario(
        "the Comet Camp",
        "a pee puddle sat beneath the bunk where the cubs stored their helmets",
        "one wobbly helmet and a trail of damp footprints",
        "told the camp leader, cleaned the bunk, and set a reminder bell",
        "the bell helped everyone remember calm body-checks before bedtime",
        "the camp bell chimed softly as every helmet rested in its place",
    ),
]


GADGETS = [
    ("a pocket moon-lamp", "held the light steady while the team searched"),
    ("a blinking rescue badge", "flashed beside the safest path"),
    ("a soft superhero towel", "soaked up the puddle without scratching the floor"),
    ("a tiny listening cape", "fluttered toward the hidden humming sound"),
]

PERKS = [
    ("a brighter signal", "Their honest plan gave the team a useful warning before the next accident."),
    ("a kinder routine", "The new routine made asking for help feel brave instead of scary."),
    ("a safer hideout", "The repaired corner became a calm place where every cub could regroup."),
    ("a helping habit", "The heroes learned to check on one another before rushing into action."),
]

HERO_NAMES = ["Luna", "Milo", "Nova", "Pip", "Tess"]
HELPER_NAMES = ["Ari", "Bea", "Sol", "Kai", "Rae"]
VILLAIN_NAMES = ["Dr. Drizzle", "The Wobble Wizard", "Captain Clatter", "The Sneaky Shadow"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

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
    scenario = SCENARIOS[params.place % len(SCENARIOS)]
    gadget_name, gadget_use = GADGETS[params.gadget % len(GADGETS)]
    perk_name, perk_meaning = PERKS[params.perk % len(PERKS)]
    setting = Setting(scenario.place)
    world = World(setting)

    hero = world.add(Entity("Hero", "character", "cub", params.hero_name))
    helper = world.add(Entity("Helper", "character", "hero", params.helper_name))
    villain = world.add(Entity("Villain", "character", "villain", params.villain_name))
    gadget = world.add(Entity("Gadget", "thing", "tool", gadget_name))

    world.facts.update(
        scenario=scenario,
        gadget_name=gadget_name,
        gadget_use=gadget_use,
        perk_name=perk_name,
        perk_meaning=perk_meaning,
        hero=hero,
        helper=helper,
        villain=villain,
        gadget=gadget,
    )

    hero.memes["brave"] = 1.0
    hero.memes["embarrassed"] = 1.0
    helper.memes["kind"] = 1.0

    world.say(
        f"In {setting.place}, {hero.label} wore a red cape and practiced a new power called cub-dim. "
        f"It made the room gently dim whenever the young hero felt worried."
    )
    world.say(
        f"Then {hero.label} noticed that {scenario.problem}. "
        f"The cub-dim power flickered, and the hero wanted to hide."
    )
    world.para()

    world.say(
        f'"I made a pee mess," {hero.label} admitted. "I need help, not a scolding."'
    )
    world.say(
        f'"Thank you for telling me," {helper.label} replied. "A superhero solves problems by being honest first."'
    )
    hero.memes["embarrassed"] = 0.0
    hero.memes["determined"] = 1.0
    helper.memes["teamwork"] = 1.0

    world.say(
        f"Together they spotted {scenario.clue}. {helper.label} lifted {gadget_name} and {gadget_use}."
    )
    world.say(
        f'"Could {villain.label} have caused this?' asked {hero.label}.'
    )
    world.say(
        f'"Maybe," said {helper.label}, "but let us test the clues before we blame anyone."'
    )
    world.para()

    world.say(
        f"They checked the door, the floor, and the nearby equipment. "
        f"Their careful problem solving showed that the puddle was an accident, not a villain's attack."
    )
    world.say(
        f"They {scenario.solution}. Then {hero.label} practiced walking to the bathroom before the cub-dim feeling grew too strong."
    )
    hero.meters["problem_solved"] = 1.0
    hero.memes["confidence"] = 1.0

    world.say(
        f"That was when a surprise appeared: {scenario.surprise}. "
        f"It was {perk_name}, a small perk born from a difficult moment."
    )
    world.say(f'"My cub-dim power did not make me weak," said {hero.label}. "It helped me notice when to ask."')
    world.say(f'"Exactly," said {helper.label}. "Real heroes use clues, kindness, and teamwork."')
    world.para()

    world.say(
        f"{villain.label} peeked around the corner, but even the pretend villain smiled. "
        f'"I thought heroes only rushed into danger," {villain.label} said.'
    )
    world.say(
        f'"Heroes also stop, tell the truth, and fix what they can," {hero.label} answered.'
    )
    world.say(
        f"{perk_meaning} {scenario.ending.capitalize()}."
    )
    world.facts["lesson"] = (
        "Honest dialogue and careful problem solving can turn an embarrassing accident "
        "into a safer habit."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scenario: Scenario = f["scenario"]  # type: ignore[assignment]
    hero: Entity = f["hero"]  # type: ignore[assignment]
    return [
        f"Write a gentle superhero story about {hero.label}, cub-dim, and a pee problem in {scenario.place}.",
        "Include dialogue, a surprise, and child-friendly problem solving.",
        "Show how an embarrassing accident can reveal a helpful perk.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    scenario: Scenario = f["scenario"]  # type: ignore[assignment]
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    villain: Entity = f["villain"]  # type: ignore[assignment]
    return [
        QAItem(
            f"Why did {hero.label}'s cub-dim power flicker?",
            f"It flickered because {hero.label} felt worried and embarrassed after noticing {scenario.problem}.",
        ),
        QAItem(
            f"How did {hero.label} and {helper.label} solve the problem?",
            f"They used honest dialogue, examined {scenario.clue}, tested the clues without blaming anyone, and then they {scenario.solution}.",
        ),
        QAItem(
            f"What surprise did the heroes discover?",
            f"They discovered that {scenario.surprise}. The difficult moment created a helpful perk instead of only causing trouble.",
        ),
        QAItem(
            f"What did {villain.label} learn?",
            f"{villain.label} learned that a real hero can stop, tell the truth, ask for help, and fix a problem carefully.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is problem solving?",
            "Problem solving means noticing a difficulty, examining clues, trying a safe plan, and changing the plan when needed.",
        ),
        QAItem(
            "Why can dialogue help solve a problem?",
            "Dialogue lets people share what they know, ask for help, and make a better decision together.",
        ),
        QAItem(
            "What is a perk?",
            "A perk is a useful extra benefit that comes along with something else.",
        ),
        QAItem(
            "What does cub-dim mean in this storyworld?",
            "Cub-dim is a gentle superhero power that dims the room when a young hero feels worried, helping the hero notice a need for support.",
        ),
    ]


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


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("topic", "pee"),
            asp.fact("topic", "perk"),
            asp.fact("topic", "cub_dim"),
            asp.fact("feature", "dialogue"),
            asp.fact("feature", "surprise"),
            asp.fact("feature", "problem_solving"),
            asp.fact("style", "superhero_story"),
        ]
    )


ASP_RULES = r"""
topic(pee).
topic(perk).
topic(cub_dim).
feature(dialogue).
feature(surprise).
feature(problem_solving).
style(superhero_story).

story_ok :-
    topic(pee),
    topic(perk),
    topic(cub_dim),
    feature(dialogue),
    feature(surprise),
    feature(problem_solving),
    style(superhero_story).

#show story_ok/0.
"""


def asp_program(show: str = "#show story_ok/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    if not any(symbol.name == "story_ok" for symbol in model):
        print("MISMATCH: ASP twin failed.")
        return 1
    sample = generate(
        StoryParams(
            hero_name="Luna",
            helper_name="Ari",
            villain_name="Dr. Drizzle",
            seed=1,
        )
    )
    required = ("pee", "perk", "cub-dim", "said", "surprise")
    lowered = sample.story.lower()
    missing = [word for word in required if word not in lowered]
    if missing:
        print("MISMATCH: generated story missing " + ", ".join(missing))
        return 1
    print("OK: ASP twin and generated story verified.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A superhero storyworld about pee, perk, and cub-dim."
    )
    parser.add_argument("--hero-name")
    parser.add_argument("--helper-name")
    parser.add_argument("--villain-name")
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
        hero_name=args.hero_name or rng.choice(HERO_NAMES),
        helper_name=args.helper_name or rng.choice(HELPER_NAMES),
        villain_name=args.villain_name or rng.choice(VILLAIN_NAMES),
        place=rng.randrange(len(SCENARIOS)),
        gadget=rng.randrange(len(GADGETS)),
        perk=rng.randrange(len(PERKS)),
    )


def generate(params: StoryParams) -> StorySample:
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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("story_ok" if any(symbol.name == "story_ok" for symbol in model) else "no model")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index in range(len(SCENARIOS)):
            params = StoryParams(
                hero_name="Luna",
                helper_name="Ari",
                villain_name="Dr. Drizzle",
                place=index,
                gadget=index % len(GADGETS),
                perk=index % len(PERKS),
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(0, args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            index += 1
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
