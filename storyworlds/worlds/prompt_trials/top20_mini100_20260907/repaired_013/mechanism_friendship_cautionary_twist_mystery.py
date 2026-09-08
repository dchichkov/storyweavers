#!/usr/bin/env python3
"""
A small mystery world about a mechanism, friendship, caution, and a twist.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
sys.path.insert(0, ROOT)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    setting: str = "the old clocktower"
    hero: str = "Lina"
    friend: str = "Moss"
    keeper: str = "the watchmaker"
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

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.name] = ent
        return ent

    def get(self, name: str) -> Entity:
        return self.entities[name]


SETTINGS = {
    "the old clocktower": {"mood": "dusty and ticking", "tags": {"mechanism", "mystery"}},
    "the lantern attic": {"mood": "quiet and gold", "tags": {"mechanism", "mystery"}},
    "the rain cellar": {"mood": "cool and echoing", "tags": {"mechanism", "mystery"}},
}

OPENINGS = [
    "By the time the bells went silent, {hero} and {friend} had already climbed into {setting} with a lantern and one careful promise.",
    "In {setting}, a small mechanism had gone wrong, and {hero} trusted {friend} to help solve the mystery.",
    "No one in {setting} could explain the soft ticking under the floor, so {hero} and {friend} went to listen for clues.",
    "At dusk, {hero} and {friend} entered {setting} because the mechanism hidden there had begun to behave strangely.",
]


@dataclass(frozen=True)
class MysteryArc:
    title: str
    premise: str
    problem: str
    dialogue: str
    action: str
    twist: str
    ending: str
    problem_answer: str
    dialogue_answer: str
    twist_answer: str


ARCS = [
    MysteryArc(
        title="The Hidden Gear",
        premise="A little brass mechanism in the wall was supposed to open the archive door only for the keeper.",
        problem="Instead, every time the key turned, the door clicked shut and a cold draft leaked out from behind it.",
        dialogue='\"We should not force it,\" said {friend}. \"Then we will listen,\" said {hero}.',
        action="They followed the draft, found a bent gear under the dust, and lifted it with a spoon handle.",
        twist="The watchmaker had hidden the real switch inside a teacup on the shelf, hoping only patient hands would find it.",
        ending="When the teacup was set in place, the archive door opened at last, and the ticking sounded friendly again.",
        problem_answer="The mechanism kept closing the archive door and sending out a cold draft.",
        dialogue_answer="Moss warned against forcing the lock, and Lina agreed to listen for clues instead.",
        twist_answer="The watchmaker had tucked the real switch inside a teacup, so the friends needed patience rather than force.",
    ),
    MysteryArc(
        title="The Stair That Whispered",
        premise="A staircase in the tower was built with a secret mechanism that should have lit each step one by one.",
        problem="But the steps stayed dark, and someone had left muddy prints heading only halfway up.",
        dialogue='\"Someone was here before us,\" whispered {hero}. \"Then let us tread softly,\" answered {friend}.',
        action="They counted the prints, matched them to a broken lantern hook, and noticed that one stair had been carved to wobble.",
        twist="The muddy prints belonged to the keeper's dog, which had carried the missing lantern downstairs to save a frightened child.",
        ending="The child returned the lantern, the steps glowed in a warm line, and the staircase stopped whispering.",
        problem_answer="The stair mechanism failed to light the tower steps, and muddy prints showed someone had passed through.",
        dialogue_answer="Lina noticed a visitor, and Moss told her to move carefully so they would not miss more clues.",
        twist_answer="The muddy tracks were from the keeper's dog, who had taken the lantern to help a frightened child.",
    ),
    MysteryArc(
        title="The Clock That Counted Twice",
        premise="An old clock in {setting} had a mechanism that rang once for every hour and once for every secret kept safely.",
        problem="That night it rang too fast, as if someone nearby had hidden a worry inside its gears.",
        dialogue='\"A secret is making the clock jump,\" said {friend}. \"Then we should be gentle with it,\" said {hero}.',
        action="They opened the back panel, found a thread caught in the spring, and unwound it without breaking the hands.",
        twist="The thread came from the keeper's sleeve, and the 'secret' was only a surprise birthday cake being rolled in from the kitchen.",
        ending="When the cake arrived, the clock struck once, then once again, and everyone laughed under the steady tick.",
        problem_answer="The clock mechanism rang too quickly because something was caught inside its gears.",
        dialogue_answer="Moss suggested gentleness, and Lina chose careful work instead of rushing.",
        twist_answer="The strange clock rhythm was caused by birthday preparations, not danger.",
    ),
    MysteryArc(
        title="The Hollow Key",
        premise="A silver key was said to awaken a hidden mechanism beneath the floorboards.",
        problem="But the key felt empty, and each time {hero} tried it, the latch rattled without opening.",
        dialogue='\"Maybe the key is not the answer,\" said {friend}. \"Maybe the answer is what it fits around,\" said {hero}.',
        action="They traced the key's shape, found a tiny seed pod lodged inside, and used it to reveal a second, smaller keyhole.",
        twist="The pod belonged to a climber's charm bracelet, and the 'hidden mechanism' was a music box left by the keeper for lost children.",
        ending="When the smaller key turned, a lullaby spilled through the room, and the mystery ended in a soft, warm note.",
        problem_answer="The hollow key could not open the latch, so the mechanism stayed shut.",
        dialogue_answer="The friends wondered whether the key was only part of the answer and stayed calm while they searched.",
        twist_answer="The hidden device was a music box, and the seed pod had only helped reveal its smaller keyhole.",
    ),
]


ASP_RULES = r"""
setting(clocktower).
setting(attic).
setting(cellar).

feature(friendship).
feature(cautionary).
feature(twist).

valid_story(S) :- setting(S), feature(friendship), feature(cautionary), feature(twist).
"""


def asp_facts() -> str:
    import asp  # lazy
    lines = []
    for s in SETTINGS:
        key = s.replace("the ", "").replace(" ", "_")
        lines.append(asp.fact("setting", key))
    lines.append(asp.fact("feature", "friendship"))
    lines.append(asp.fact("feature", "cautionary"))
    lines.append(asp.fact("feature", "twist"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mystery story world with a mechanism, friendship, caution, and a twist.")
    ap.add_argument("--setting", choices=list(SETTINGS))
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--keeper")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(["Lina", "Tess", "Noor", "Iris", "Pip"])
    friend = args.friend or rng.choice(["Moss", "Jori", "Ned", "Vale", "Suki"])
    keeper = args.keeper or rng.choice(["the watchmaker", "the attic keeper", "the lantern keeper"])
    if hero == friend:
        raise StoryError("The hero and friend must be different characters.")
    return StoryParams(setting=setting, hero=hero, friend=friend, keeper=keeper)


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join((params.setting, params.hero, params.friend, params.keeper))
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text))


def _fill(text: str, data: dict[str, object]) -> str:
    return text.format(**data)


def _story_lines(world: World) -> list[str]:
    f = world.facts
    arc: MysteryArc = f["arc"]
    return [
        _fill(OPENINGS[f["opening_variant"]], f),
        _fill(arc.premise, f),
        _fill(arc.problem, f),
        _fill(arc.dialogue, f),
        _fill(arc.action, f),
        _fill(arc.twist, f),
        _fill(arc.ending, f),
    ]


def generate(params: StoryParams) -> StorySample:
    seed = _stable_seed(params)
    arc = ARCS[seed % len(ARCS)]
    world = World(setting=params.setting)

    hero = world.add(Entity(name=params.hero, kind="character", memes={"curious": 1.0, "cautious": 1.0}))
    friend = world.add(Entity(name=params.friend, kind="character", memes={"faithful": 1.0, "cautious": 1.0}))
    keeper = world.add(Entity(name=params.keeper, kind="adult", memes={"mysterious": 1.0}))
    world.add(Entity(name="the mechanism", kind="device", meters={"tension": 1.0}, memes={"secret": 1.0}))
    world.add(Entity(name="the lantern", kind="tool", meters={"light": 1.0}))
    world.facts.update(
        hero=hero.name,
        friend=friend.name,
        keeper=keeper.name,
        setting=params.setting,
        arc=arc,
        opening_variant=seed % len(OPENINGS),
    )

    story = "\n\n".join(_story_lines(world))
    prompts = [
        f"Write a child-facing mystery about {params.hero} and {params.friend} in {params.setting}.",
        "Include a small mechanism, a cautious choice, and a twist.",
        "Make sure the story includes spoken dialogue that changes what the characters do.",
    ]
    story_qa = [
        QAItem(
            question=f"What was wrong with the mechanism in \"{arc.title}\"?",
            answer=arc.problem_answer,
        ),
        QAItem(
            question="What did the friends say to each other before acting?",
            answer=arc.dialogue_answer,
        ),
        QAItem(
            question="What was the twist at the end?",
            answer=arc.twist_answer,
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the mystery solved and {world.facts['keeper']}'s secret made harmless and kind.",
        ),
    ]
    world_qa = [
        QAItem(question="What is friendship?", answer="Friendship is a caring bond where people help and trust each other."),
        QAItem(question="What is caution?", answer="Caution means being careful and not rushing into danger."),
        QAItem(question="What is a twist in a mystery?", answer="A twist is a surprising change that reveals the truth in a new way."),
        QAItem(question="What is a mechanism?", answer="A mechanism is a set of parts that work together to make something move or open."),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for e in sample.world.entities.values():
            print(f"{e.name}: kind={e.kind}, meters={dict(e.meters)}, memes={dict(e.memes)}")
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def _py_valid() -> list[tuple]:
    return [(s.replace("the ", "").replace(" ", "_"),) for s in SETTINGS]


def _asp_valid() -> list[tuple]:
    import asp  # lazy
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(_py_valid())
    cl = set(_asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches python ({len(py)} settings).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        for item in _asp_valid():
            print(item[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTINGS:
            params = StoryParams(setting=setting, hero="Lina", friend="Moss", keeper="the watchmaker", seed=base_seed)
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

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
