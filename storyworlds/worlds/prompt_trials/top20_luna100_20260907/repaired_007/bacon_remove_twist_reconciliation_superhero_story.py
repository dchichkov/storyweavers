#!/usr/bin/env python3
"""
A tiny Storyweavers world about a young superhero, a strip of bacon, and
a reconciliation after a surprising mistake.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    @property
    def phrase(self) -> str:
        return self.label or self.id.replace("_", " ")


@dataclass
class Place:
    id: str
    label: str
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
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
class StoryArc:
    key: str
    problem: str
    action: str
    result: str
    opening: tuple[str, str]
    trouble: tuple[str, str]
    twist: tuple[str, str]
    repair: tuple[str, str]
    ending: tuple[str, str]


ARCS = (
    StoryArc(
        key="scent_signal",
        problem="a bacon smell drifted into the rescue station and made the alarm dog chase the wrong cart",
        action="remove the bacon from the control table and explain the mistake",
        result="the alarm dog returned to the real rescue bell",
        opening=(
            "In {place}, {hero} wore a bright cape and watched over the morning rescue station.",
            "{hero} had promised to keep every neighbor safe, even when the city felt busy.",
        ),
        trouble=(
            "Then a warm strip of bacon slid beside the signal bell.",
            "The alarm dog sniffed it, dashed after a snack cart, and left the bell alone.",
        ),
        twist=(
            '"I did not put the bacon there," said {hero}. "Wait—your lunch tin is open!"',
            "{friend} looked surprised. The bacon had fallen from the tin when the wind flipped its lid.",
        ),
        repair=(
            '"I am sorry I blamed you," said {friend}. "Let us remove it together."',
            "{hero} lifted the bacon away while {friend} closed the tin and called the dog back.",
        ),
        ending=(
            "The true bell rang, the dog returned, and the rescue station shone safely again.",
            "{hero} and {friend} shared a smile beneath the cape, stronger because they had made peace.",
        ),
    ),
    StoryArc(
        key="rooftop_lunch",
        problem="a piece of bacon stuck to a rooftop signal mirror and hid a warning flash",
        action="remove the bacon carefully and listen to the friend who caused the accident",
        result="the mirror flashed clearly toward the firefighters",
        opening=(
            "On the rooftop of {place}, {hero} practiced superhero signals beside a silver mirror.",
            "{friend} brought lunch while {hero} scanned the streets below.",
        ),
        trouble=(
            "A gust lifted the lunch wrapper, and bacon slapped onto the mirror with a soft plop.",
            "The warning flash vanished, so {hero} thought {friend} had played a careless trick.",
        ),
        twist=(
            '"It was not a trick," said {friend}. "The gust pulled my lunch away."',
            "The wind had made the mess. Both friends saw that the accident was not meant to hurt anyone.",
        ),
        repair=(
            '"I believe you," said {hero}. "Help me remove the bacon without scratching the mirror."',
            "They used a clean cloth, then tied every wrapper down before trying the signal again.",
        ),
        ending=(
            "The mirror flashed across the roofs, and help found the waiting family below.",
            "The two friends shared the rescued lunch and let the wind carry only their happy cheers.",
        ),
    ),
    StoryArc(
        key="bridge_patrol",
        problem="bacon grease made the handle of the hero's safety rope slippery",
        action="remove the greasy wrapper, wash the handle, and forgive the friend who dropped it",
        result="the safety rope held firm during the bridge rescue",
        opening=(
            "Near {place}, {hero} patrolled a little bridge with a safety rope and a brave blue cape.",
            "{friend} carried a picnic basket for the people waiting on the other side.",
        ),
        trouble=(
            "The basket tipped, and bacon grease spread across the rope handle.",
            "{hero} reached for it, slipped, and turned angrily toward {friend}.",
        ),
        twist=(
            '"I was trying to help," said {friend}. "The basket latch broke all by itself."',
            "{hero} saw the broken latch and understood that the spill had been an accident.",
        ),
        repair=(
            '"Then we can fix it together," said {hero}. "I am sorry I shouted."',
            "They removed the greasy wrapper, washed the handle, and tested the rope twice.",
        ),
        ending=(
            "The rope held strong as {hero} helped everyone cross the bridge.",
            "{friend} repaired the basket, and their friendship felt steady as a superhero shield.",
        ),
    ),
)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    friend_name: str
    hero_gender: str = "girl"
    friend_gender: str = "boy"
    seed: Optional[int] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)


PLACES = {
    "rescue_station": Place("rescue_station", "the sunny rescue station", {"city", "safe"}),
    "rooftop": Place("rooftop", "the high rooftop", {"city", "windy"}),
    "bridge": Place("bridge", "the little city bridge", {"city", "crossing"}),
}

NAMES = {
    "girl": ["Luna", "Maya", "Iris", "Nia"],
    "boy": ["Theo", "Milo", "Jay", "Owen"],
}

CURATED = [
    StoryParams("rescue_station", "Luna", "Theo", "girl", "boy", 10),
    StoryParams("rooftop", "Maya", "Iris", "girl", "girl", 20),
    StoryParams("bridge", "Nia", "Owen", "girl", "boy", 30),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A superhero story about bacon and reconciliation.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--hero-gender", choices=NAMES)
    parser.add_argument("--friend-gender", choices=NAMES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero_gender = args.hero_gender or "girl"
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(NAMES[hero_gender])
    choices = [name for name in NAMES[friend_gender] if name != hero]
    friend = args.friend or rng.choice(choices)
    return StoryParams(
        place=args.place or rng.choice(list(PLACES)),
        hero_name=hero,
        friend_name=friend,
        hero_gender=hero_gender,
        friend_gender=friend_gender,
        seed=args.seed,
    )


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}.")
    if not params.hero_name.strip() or not params.friend_name.strip():
        raise StoryError("Hero and friend names must not be empty.")
    if params.hero_name.casefold() == params.friend_name.casefold():
        raise StoryError("The hero and friend must have different names.")

    rng = random.Random(params.seed if params.seed is not None else 0)
    arc = rng.choice(ARCS)
    world = World(PLACES[params.place])
    hero = world.add(Entity(params.hero_name, "character", params.hero_gender, params.hero_name, "hero"))
    friend = world.add(Entity(params.friend_name, "character", params.friend_gender, params.friend_name, "friend"))
    bacon = world.add(Entity("bacon", "food", "bacon", "a strip of bacon"))
    signal = world.add(Entity("signal", "thing", "signal", "rescue signal"))

    values = {"place": world.place.label, "hero": params.hero_name, "friend": params.friend_name}
    for line in arc.opening:
        world.say(line.format(**values))
    world.para()

    bacon.meters["misplaced"] = 1
    signal.meters["hidden"] = 1
    hero.memes["confused"] = 1
    friend.memes["worried"] = 1
    for line in arc.trouble:
        world.say(line.format(**values))
    world.para()

    hero.memes["curious"] = 1
    friend.memes["honest"] = 1
    for line in arc.twist:
        world.say(line.format(**values))
    world.para()

    bacon.meters["removed"] = 1
    signal.meters["clear"] = 1
    hero.memes["forgiving"] = 1
    friend.memes["forgiven"] = 1
    for line in arc.repair:
        world.say(line.format(**values))
    world.para()

    hero.memes["joy"] = 1
    friend.memes["joy"] = 1
    for line in arc.ending:
        world.say(line.format(**values))

    world.facts.update(
        hero=hero,
        friend=friend,
        bacon=bacon,
        signal=signal,
        place=world.place,
        arc=arc,
        problem=arc.problem,
        action=arc.action,
        result=arc.result,
        ending=arc.ending[-1].format(**values),
        twist="The bacon trouble was an accident caused by wind, a broken latch, or an open lunch tin.",
        reconciled=True,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    facts = world.facts
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            'Write a gentle superhero story that includes the words "bacon" and "remove".',
            f"Tell how {facts['hero'].phrase} and {facts['friend'].phrase} reconcile after {facts['problem']}.",
            "Show a surprising twist and end with a concrete sign that friendship was repaired.",
        ],
        story_qa=[
            QAItem(
                "What problem did the superhero friends face?",
                f"They faced this problem: {facts['problem']}.",
            ),
            QAItem(
                "What twist changed what they believed?",
                f"The twist was that {facts['twist'].lower()}",
            ),
            QAItem(
                "How did they reconcile?",
                f"They reconciled when they chose to {facts['action']}. As a result, {facts['result']}.",
            ),
            QAItem(
                "What showed that their friendship was repaired?",
                facts["ending"],
            ),
        ],
        world_qa=[
            QAItem(
                "Why is it useful to remove grease from a handle?",
                "Removing grease makes a handle cleaner and easier to hold safely.",
            ),
            QAItem(
                "What is reconciliation?",
                "Reconciliation is making peace after a disagreement by listening, apologizing, and choosing to work together again.",
            ),
        ],
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(f"  {entity.id}: meters={meters}, memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
misplaced(bacon).
hidden(signal) :- misplaced(bacon).
removed(bacon) :- honest(friend), listens(hero), misplaced(bacon).
clear(signal) :- removed(bacon).
reconciled(hero, friend) :- clear(signal).
outcome(reconciled) :- reconciled(hero, friend).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("hero", "hero"),
            asp.fact("friend", "friend"),
            asp.fact("bacon", "bacon"),
            asp.fact("signal", "signal"),
            asp.fact("honest", "friend"),
            asp.fact("listens", "hero"),
        ]
    )


def asp_program(show: str = "#show outcome/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
        if not asp.atoms(model, "outcome"):
            print("ASP parity failed: no reconciliation outcome.")
            return 1
    except Exception as exc:
        print(f"ASP smoke test failed: {exc}")
        return 1
    try:
        sample = generate(StoryParams("rescue_station", "Luna", "Theo", seed=1))
        if "bacon" not in sample.story or "remove" not in sample.story.lower():
            print("Story smoke test failed: required words missing.")
            return 1
        if not sample.world or not sample.world.facts["reconciled"]:
            print("Story smoke test failed: reconciliation missing.")
            return 1
    except Exception as exc:
        print(f"Generation smoke test failed: {exc}")
        return 1
    print("OK: smoke tests passed.")
    return 0


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        model = asp.one_model(asp_program("#show outcome/1."))
        print(asp.atoms(model, "outcome"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen = set()
        for offset in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            local_args = argparse.Namespace(**vars(args))
            local_args.seed = seed
            params = resolve_params(local_args, random.Random(seed))
            params.seed = seed
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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
