#!/usr/bin/env python3
"""
A small superhero-story world about bacon, a removal, a twist, and a
reconciliation.

A young hero tries to remove bacon from a shared lunch after it causes trouble.
The situation twists when the real problem is not the bacon itself but a hurt
feeling and a misunderstanding. By talking, sharing, and making a better plan,
the characters reconcile and the meal becomes safe and kind again.
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

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str = "Nova"
    helper_name: str = "Dash"
    friend_name: str = "Pip"
    setting: str = "rooftop lunch"
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


HERO_NAMES = ["Nova", "Spark", "Comet", "Mira", "Beacon"]
HELPER_NAMES = ["Dash", "Pulse", "Echo", "Byte", "Quill"]
FRIEND_NAMES = ["Pip", "Toby", "Lia", "Rin", "Momo"]
SETTINGS = [
    "rooftop lunch",
    "school picnic",
    "community kitchen",
    "park bench snack break",
    "team clubhouse dinner",
]

ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(H) :- helper_name(H).
friend(F) :- friend_name(F).
bacon_present :- food(bacon).
removed(bacon) :- action(remove, bacon).
twist :- misunderstanding.
reconciliation :- apology, shared_plan.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("hero_name", "hero"),
            asp.fact("helper_name", "helper"),
            asp.fact("friend_name", "friend"),
            asp.fact("food", "bacon"),
            asp.fact("action", "remove", "bacon"),
            asp.fact("misunderstanding"),
            asp.fact("apology"),
            asp.fact("shared_plan"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show twist/0.\n#show reconciliation/0.\n#show removed/1."))
    got = {(sym.name, tuple(a.string if a.type == a.type.String else a.number if a.type == a.type.Number else a.name for a in sym.arguments)) for sym in model}
    want = {("twist", ()), ("reconciliation", ()), ("removed", ("bacon",))}
    if got == want:
        print("OK: ASP and Python parity looks good.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("ASP:", sorted(got))
    print("PY :", sorted(want))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero story world about bacon, remove, twist, and reconciliation.")
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--friend")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != hero])
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n not in {hero, helper}])
    if len({hero, helper, friend}) < 3:
        raise StoryError("The hero, helper, and friend must be different characters.")
    return StoryParams(
        hero_name=hero,
        helper_name=helper,
        friend_name=friend,
        setting=args.setting or rng.choice(SETTINGS),
    )


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed if params.seed is not None else f"{params.hero_name}:{params.helper_name}:{params.friend_name}:{params.setting}")
    world = World()

    hero = world.add(Entity(id="hero", kind="character", label=params.hero_name, type="superhero", memes={"hope": 2.0, "worry": 0.0}))
    helper = world.add(Entity(id="helper", kind="character", label=params.helper_name, type="sidekick", memes={"curiosity": 1.0}))
    friend = world.add(Entity(id="friend", kind="character", label=params.friend_name, type="child", memes={"hurt": 1.0, "hope": 0.5}))
    bacon = world.add(Entity(id="bacon", kind="food", label="bacon", type="food", owner="friend", meters={"smell": 1.0, "heating": 0.0}, memes={"crunch": 1.0}))
    lunchbox = world.add(Entity(id="lunchbox", kind="container", label="lunch tray", type="tray", meters={"fullness": 1.0}, memes={"order": 0.5}))

    world.say(f"It was a bright {params.setting}, and {params.hero_name} arrived in a cape with {params.helper_name} at their side.")
    world.say(f"On the table sat a lunch tray with bacon that did not belong at the center of the meal, because {params.friend_name} looked upset.")
    world.say(f'“I can remove the bacon,” {params.hero_name} said. “That will fix it.”')
    world.say(f'“Wait,” said {params.helper_name}, “let us find out what is really going on.”')

    bacon.meters["smell"] = 1.5
    lunchbox.meters["fullness"] = 0.8
    hero.memes["confidence"] = 1.0

    world.say(f"{params.hero_name} tried to remove the bacon at once, but the twist was that the trouble was bigger than the snack.")
    world.say(f'{params.friend_name} spoke up softly: “I was saving that piece for later, and nobody asked me.”')
    friend.memes["hurt"] = 2.0
    hero.memes["worry"] = 1.5

    world.say(f'“Oh,” said {params.hero_name}. “I thought the bacon was the problem.”')
    world.say(f'“The bacon is not the problem,” said {params.helper_name}. “The problem is feeling ignored.”')

    world.say("The hero stepped back, and the caped helper laid out a better plan: listen first, then share the food fairly.")
    world.say(f'“I am sorry,” {params.hero_name} said to {params.friend_name}. “I should have asked before I tried to remove it.”')
    world.say(f'“I am sorry too,” said {params.friend_name}. “I should have said what I wanted instead of scowling.”')

    world.say("That apology brought a reconciliation that felt warmer than the sun on the rooftop.")
    world.say(f'Together they moved the bacon to one side of the tray, split it carefully, and added fruit so everyone had enough.')
    bacon.owner = "friend"
    bacon.meters["smell"] = 0.7
    lunchbox.meters["fullness"] = 1.0
    hero.memes["hope"] = 2.0
    helper.memes["curiosity"] = 1.5
    friend.memes["hurt"] = 0.0
    friend.memes["hope"] = 2.0

    world.say(f"{params.hero_name} smiled beneath the cape. “The best fix was not just removing bacon. It was understanding each other.”")
    world.say(f'“Yes,” said {params.helper_name}. “A true hero solves the whole problem.”')
    world.say(f"By the end of the {params.setting}, the tray was neat, the friends were laughing, and the bacon was shared instead of fought over.")

    world.facts.update(
        hero=hero,
        helper=helper,
        friend=friend,
        bacon=bacon,
        lunchbox=lunchbox,
        twist=True,
        reconciliation=True,
        removed_bacon=True,
    )

    prompts = [
        f"Write a superhero story about {params.hero_name} trying to remove bacon at a {params.setting}.",
        f"Include a twist where the bacon is not the real problem, and end with reconciliation.",
        f"Make {params.hero_name}, {params.helper_name}, and {params.friend_name} speak to each other in a child-friendly way.",
    ]

    story_qa = [
        QAItem(
            question="What did the hero try to remove?",
            answer="The hero tried to remove the bacon from the lunch tray.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer="The twist was that the bacon was not the real problem; the real problem was that the friend felt ignored.",
        ),
        QAItem(
            question="How did the characters reconcile?",
            answer="They apologized, listened to each other, and shared the food fairly.",
        ),
        QAItem(
            question="What proved the ending was happy?",
            answer="The tray was neat, the friends were laughing, and the bacon was shared instead of fought over.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is bacon?",
            answer="Bacon is a salty food made from strips of cured meat, often cooked until crisp.",
        ),
        QAItem(
            question="What does remove mean?",
            answer="Remove means to take something away from where it was before.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people make peace again after a disagreement by understanding each other and starting fresh.",
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
        for key, ent in sample.world.entities.items():
            print(f"{key}: {ent.label} meters={ent.meters} memes={ent.memes}")
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print("\n== story qa ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")
        print("\n== world qa ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show twist/0.\n#show reconciliation/0.\n#show removed/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for i in range(len(SETTINGS)):
            params = StoryParams(
                hero_name=HERO_NAMES[i % len(HERO_NAMES)],
                helper_name=HELPER_NAMES[i % len(HELPER_NAMES)],
                friend_name=FRIEND_NAMES[i % len(FRIEND_NAMES)],
                setting=SETTINGS[i],
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
