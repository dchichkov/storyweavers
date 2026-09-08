#!/usr/bin/env python3
"""
A gentle nursery-rhyme world about a fond buckaroo, magical Lego bricks,
and a happy ending.
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
class StoryParams:
    setting: str = "the moonlit meadow"
    hero: str = "Luna"
    friend: str = "Pip"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.name] = entity
        return entity


SETTING_REGISTRY = {
    "the moonlit meadow": {"mood": "silver and soft"},
    "the clover hill": {"mood": "green and bright"},
    "the humming barn": {"mood": "warm and golden"},
}


@dataclass(frozen=True)
class RhymeArc:
    title: str
    problem: str
    choice: str
    action: str
    result: str
    ending: str
    problem_answer: str
    choice_answer: str
    result_answer: str


ARCS = [
    RhymeArc(
        "The Little Lego Gate",
        "A wind had scattered the Lego pieces, and the moon-cow could not pass through the meadow gate.",
        "\"Do not fret,\" said the fond buckaroo. \"We will build a way for our friend.\"",
        "Luna sorted red, blue, and yellow bricks while Pip clicked them together in a tidy row.",
        "A tiny magic star shone on the finished gate, and the moon-cow stepped safely home.",
        "the new Lego gate sparkled while every cow wore a daisy crown",
        "The wind scattered the Lego pieces and blocked the moon-cow at the meadow gate.",
        "The buckaroo chose to help the moon-cow instead of giving up.",
        "The friends rebuilt the gate, and magic made it safe and bright.",
    ),
    RhymeArc(
        "The Buckaroo's Blue Boot",
        "One blue boot slipped into a puddle, leaving the buckaroo unable to dance for the barn parade.",
        "\"I am fond of your brave heart,\" said Pip. \"Let us mend the boot before the music starts.\"",
        "They built a little Lego moon beneath the boot and whispered a kind spell over every brick.",
        "The boot bounced up, dry and light, and the buckaroo led the parade with a jolly hop.",
        "the blue boot tapped twice as the whole barn sang, \"Hip-hip-hooray!\"",
        "A blue boot fell into a puddle and stopped the buckaroo from dancing.",
        "The friends decided to repair the boot together before the parade.",
        "The Lego moon and kind spell made the boot dry and bouncy again.",
    ),
    RhymeArc(
        "The Starry Stable",
        "The stable roof lost its star, so the sleepy ponies could not find their warm beds.",
        "\"A roof can be rebuilt,\" said Luna. \"A friend should never sleep beneath the rain.\"",
        "The buckaroo stacked Lego bricks into a bright star and carried it up with Pip's help.",
        "The magic star lit the stable, and the ponies curled up in cozy straw.",
        "the stable star winked above a row of peaceful pony noses",
        "The stable lost its star and the ponies could not find their beds.",
        "Luna and Pip chose to rebuild the roof so the ponies would be safe and dry.",
        "Their Lego star lit the stable and guided the ponies to warm straw.",
    ),
    RhymeArc(
        "The Clover Crown",
        "A shy foal had no crown for the meadow feast and hid behind a tall green stone.",
        "\"Come out, little foal,\" called the fond buckaroo. \"We have bricks and time for you.\"",
        "They made a Lego crown with clover leaves tucked between the bricks.",
        "The magic crown glowed gently, and the foal joined the feast with a proud little prance.",
        "the clover crown rested on the foal while bees hummed a tiny tune",
        "The shy foal hid because it had no crown for the meadow feast.",
        "The buckaroo invited the foal out and promised to make a crown.",
        "The Lego and clover crown helped the foal feel brave enough to join the feast.",
    ),
    RhymeArc(
        "The Rainbow Corral",
        "Rain filled the corral, and the lambs stood shivering on a little wooden box.",
        "\"We must make a bridge,\" said Pip. \"The lambs are counting on us.\"",
        "Luna and the buckaroo built a rainbow bridge from Lego bricks, one color at a time.",
        "Magic lifted the bridge above the puddles, and every lamb skipped to the dry hill.",
        "the rainbow bridge shone while the lambs bleated a happy song",
        "Rain flooded the corral and left the lambs shivering on a box.",
        "The friends chose to build a bridge so the lambs could reach dry ground.",
        "The magical Lego bridge carried every lamb safely to the hill.",
    ),
]


OPENINGS = [
    "Ride, ride, fond buckaroo, beneath the sky so wide; {hero} rode with {friend} close by {setting}.",
    "Clip-clop, tip-top, hear the meadow tune: {hero}, the fond buckaroo, rode beneath the moon.",
    "In {setting}, where silver grasses sway, {hero} and {friend} began a bright adventure one day.",
    "A Lego brick went click and clack as {hero} rode the pony track.",
]


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum((i + 1) * ord(c) for i, c in enumerate("|".join(
        [params.setting, params.hero, params.friend]
    )))


def _fill(text: str, facts: dict[str, object]) -> str:
    return text.format(**facts)


def _cap(text: str) -> str:
    return text[:1].upper() + text[1:]


def _story_lines(world: World) -> list[str]:
    facts = world.facts
    arc: RhymeArc = facts["arc"]
    opening = _fill(OPENINGS[facts["opening_variant"]], facts)
    problem = _fill(arc.problem, facts)
    choice = _fill(arc.choice, facts)
    action = _fill(arc.action, facts)
    result = _fill(arc.result, facts)
    ending = _fill(arc.ending, facts)
    hero = facts["hero"]
    friend = facts["friend"]

    forms = [
        [
            f"{opening} This little rhyme is called \"{arc.title}.\"",
            f"{problem} The trouble was small, but it mattered to their friends.",
            f"{choice} \"Will it work?\" asked {friend}. \"Kind hands can make magic,\" said {hero}.",
            action,
            result,
            f"{_cap(ending)}. And that was a happy ending, bright as a bell.",
        ],
        [
            opening,
            f"\"What shall we do?\" asked {friend}. {problem}",
            f"{hero} tipped their hat. {choice}",
            f"{action} Click, clack, click!",
            f"{result} The meadow grew merry once more.",
            f"At bedtime, {ending}.",
        ],
        [
            f"One, two, three, the hoofbeats ran. {opening}",
            f"Then came the worry: {problem}",
            f"\"We will help,\" said {hero}. {choice}",
            action,
            f"{result} Pip laughed, and Luna laughed too.",
            f"Under the stars, {ending}. So the rhyme was done.",
        ],
        [
            f"{opening} Listen close, for magic is near.",
            f"{_cap(problem)}",
            f"\"Friends together, brave and fond,\" said {hero}. {choice}",
            action,
            f"{result} The happy sound reached every corner of {facts['setting']}.",
            f"{_cap(ending)}, and all the little hearts felt warm.",
        ],
    ]
    return forms[facts["structure_variant"]]


ASP_RULES = r"""
setting(moonlit_meadow).
setting(clover_hill).
setting(humming_barn).
feature(magic).
feature(happy_ending).
can_tell_story(S) :- setting(S), feature(magic), feature(happy_ending).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for setting in SETTING_REGISTRY:
        key = setting.replace("the ", "").replace(" ", "_")
        lines.append(asp.fact("setting", key))
    lines.extend([
        asp.fact("feature", "magic"),
        asp.fact("feature", "happy_ending"),
    ])
    return "\n".join(lines)


def asp_program(show: str = "#show can_tell_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A nursery rhyme about a fond buckaroo, Lego, and magic."
    )
    parser.add_argument("--setting", choices=list(SETTING_REGISTRY))
    parser.add_argument("--hero")
    parser.add_argument("--friend")
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
    setting = args.setting or rng.choice(list(SETTING_REGISTRY))
    hero = args.hero or rng.choice(["Luna", "Bess", "Rory", "Mabel"])
    friend = args.friend or rng.choice(["Pip", "Toby", "Nell", "Jo"])
    if hero == friend:
        raise StoryError("The buckaroo and friend must have different names.")
    return StoryParams(setting=setting, hero=hero, friend=friend)


def generate(params: StoryParams) -> StorySample:
    seed = _stable_seed(params)
    arc = ARCS[seed % len(ARCS)]
    world = World(setting=params.setting)

    hero = world.add(Entity(
        params.hero,
        "buckaroo",
        meters={"balance": 1.0, "energy": 0.8},
        memes={"fondness": 1.0, "courage": 1.0},
    ))
    friend = world.add(Entity(
        params.friend,
        "friend",
        meters={"helpfulness": 1.0},
        memes={"kindness": 1.0, "hope": 1.0},
    ))
    lego = world.add(Entity(
        "the Lego bricks",
        "toy",
        meters={"pieces": 1.0, "shape": 0.0},
        memes={"magic": 0.8},
    ))
    world.add(Entity(
        "the meadow magic",
        "magic",
        meters={"sparkle": 1.0},
        memes={"joy": 1.0},
    ))

    world.facts.update({
        "hero": hero.name,
        "friend": friend.name,
        "setting": params.setting,
        "arc": arc,
        "opening_variant": (seed // len(ARCS)) % len(OPENINGS),
        "structure_variant": (seed // (len(ARCS) * len(OPENINGS))) % 4,
        "theme": "fondness, buckaroo courage, Lego, magic, and a happy ending",
    })

    story = "\n\n".join(_story_lines(world))
    prompts = [
        f"Write a nursery rhyme about a fond buckaroo named {params.hero}.",
        f"Tell a magical Lego story in {params.setting} with a happy ending.",
        "Write a gentle child-facing rhyme where friends solve a problem together.",
    ]
    story_qa = [
        QAItem(
            question=f"What problem did {params.hero} and {params.friend} face?",
            answer=arc.problem_answer,
        ),
        QAItem(
            question="How did the friends show fondness and courage?",
            answer=arc.choice_answer,
        ),
        QAItem(
            question="What did the Lego magic change?",
            answer=arc.result_answer,
        ),
        QAItem(
            question=f"How does \"{arc.title}\" end?",
            answer=f"It ends with {arc.ending.format(hero=params.hero, friend=params.friend, setting=params.setting)}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a buckaroo?",
            answer="A buckaroo is a cheerful cowboy or cowgirl who rides and cares for animals.",
        ),
        QAItem(
            question="What is Lego?",
            answer="Lego is a building toy made from small pieces that fit together.",
        ),
        QAItem(
            question="What is magic in this story world?",
            answer="Magic is a gentle wonder that helps caring friends make good things happen.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending shows that the danger is over and the characters are safe, hopeful, or joyful.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
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
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            print(
                f"{entity.name}: kind={entity.kind}, "
                f"meters={dict(entity.meters)}, memes={dict(entity.memes)}"
            )
    if qa:
        print("\n== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def _valid_python() -> list[str]:
    return sorted(
        setting.replace("the ", "").replace(" ", "_")
        for setting in SETTING_REGISTRY
    )


def _asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "can_tell_story")))


def asp_verify() -> int:
    python_values = {(name,) for name in _valid_python()}
    asp_values = set(_asp_valid())
    if python_values == asp_values:
        print(f"OK: clingo gate matches python ({len(python_values)} settings).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python only:", sorted(python_values - asp_values))
    print("clingo only:", sorted(asp_values - python_values))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        status = asp_verify()
        if status:
            raise SystemExit(status)
        for seed in range(3):
            params = StoryParams(
                setting=list(SETTING_REGISTRY)[seed % len(SETTING_REGISTRY)],
                hero="Luna",
                friend="Pip",
                seed=seed,
            )
            sample = generate(params)
            if not sample.story.strip() or "{" in sample.story:
                raise SystemExit("Generated story verification failed.")
        print("OK: generated stories pass.")
        return
    if args.asp:
        for item in _asp_valid():
            print(item[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTING_REGISTRY:
            samples.append(generate(StoryParams(
                setting=setting,
                hero="Luna",
                friend="Pip",
            )))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            current_seed = base_seed + index
            index += 1
            rng = random.Random(current_seed)
            params = resolve_params(args, rng)
            params.seed = current_seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

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
