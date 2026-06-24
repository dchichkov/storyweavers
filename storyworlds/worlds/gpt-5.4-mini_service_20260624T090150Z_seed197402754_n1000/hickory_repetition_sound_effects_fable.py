#!/usr/bin/env python3
"""
A small fable-style storyworld about a hickory tree, a repeated mistake, and a
sound-effect turn that teaches a gentle lesson.

Premise:
- A small animal wants hickory nuts.
- A greedy choice or careless choice makes trouble.
- Repetition builds the rhythm of the fable.
- Sound effects mark the physical action and the emotional beat.
- The ending shows a changed choice and a learned lesson.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

HICKORY = "hickory"
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"squirrel", "fox", "rabbit", "crow", "mouse"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class StoryParams:
    hero: str
    lesson: str
    seed: Optional[int] = None


@dataclass
class Choice:
    id: str
    hero: str
    lesson: str
    repeated_action: str
    repeated_sound: str
    final_action: str
    final_sound: str
    trouble: str
    turn: str
    resolution: str


HEROES = {
    "squirrel": {
        "label": "a little squirrel",
        "type": "squirrel",
        "traits": ["quick", "curious"],
        "likes": "hickory nuts",
    },
    "crow": {
        "label": "a black crow",
        "type": "crow",
        "traits": ["sharp-eyed", "busy"],
        "likes": "shiny seeds",
    },
    "rabbit": {
        "label": "a small rabbit",
        "type": "rabbit",
        "traits": ["gentle", "eager"],
        "likes": "sweet roots",
    },
}

CHOICES = {
    "squirrel": Choice(
        id="squirrel",
        hero="squirrel",
        lesson="share",
        repeated_action="snatch one more hickory nut",
        repeated_sound="nip-nip",
        final_action="leave a few nuts for others",
        final_sound="tap-tap",
        trouble="the basket kept getting emptier",
        turn="the pile looked smaller each time the squirrel hurried back",
        resolution="the squirrel set the last nuts on a stump so the other animals could find them",
    ),
    "crow": Choice(
        id="crow",
        hero="crow",
        lesson="listen",
        repeated_action="peek at the hickory shell again and again",
        repeated_sound="clack-clack",
        final_action="listen before touching the shell",
        final_sound="click",
        trouble="the shell would not open the same way twice",
        turn="the crow's quick pecks only made a louder fuss",
        resolution="the crow waited, watched, and then opened it the careful way",
    ),
    "rabbit": Choice(
        id="rabbit",
        hero="rabbit",
        lesson="be patient",
        repeated_action="hop back to the hickory tree for one more try",
        repeated_sound="thump-thump",
        final_action="wait for the wind to shake down the nuts",
        final_sound="whoosh",
        trouble="the rabbit kept arriving too soon",
        turn="each hop made the rabbit miss the nuts still high in the branches",
        resolution="the rabbit sat still under the tree and let the wind help",
    ),
}

LESSONS = ["share", "listen", "be patient"]


@dataclass
class World:
    hero: Entity
    tree: Entity
    basket: Entity
    choice: Choice
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    repeated_count: int = 0
    fixed: bool = False
    sound_log: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_world(params: StoryParams) -> World:
    hero_cfg = HEROES[params.hero]
    choice = CHOICES[params.hero]
    hero = Entity(
        id=params.hero,
        kind="character",
        type=hero_cfg["type"],
        label=hero_cfg["label"],
        meters={"want": 0.0, "trouble": 0.0, "calm": 0.0},
        memes={"greed": 0.0, "patience": 0.0, "kindness": 0.0},
    )
    tree = Entity(
        id="hickory_tree",
        kind="thing",
        type="tree",
        label="the hickory tree",
        meters={"nuts": 3.0},
    )
    basket = Entity(
        id="basket",
        kind="thing",
        type="basket",
        label="a little basket",
        meters={"nuts": 0.0},
    )
    return World(hero=hero, tree=tree, basket=basket, choice=choice)


def shake_sound(world: World) -> str:
    return {
        "squirrel": "nip-nip",
        "crow": "clack-clack",
        "rabbit": "thump-thump",
    }[world.choice.hero]


def turn_sound(world: World) -> str:
    return {
        "squirrel": "tap-tap",
        "crow": "click",
        "rabbit": "whoosh",
    }[world.choice.hero]


def tell(world: World) -> None:
    hero = world.hero
    choice = world.choice
    tree = world.tree
    basket = world.basket

    world.say(
        f"Under the hickory tree lived {hero.label}, and {hero.name_or_label()} loved the sweet nuts that fell in autumn."
    )
    world.say(
        f"Each morning, {hero.name_or_label()} went to the tree and said, \"One more for the basket, one more for the day.\""
    )
    world.para()

    hero.meters["want"] += 1
    while tree.meters["nuts"] > 0 and world.repeated_count < 2:
        world.repeated_count += 1
        tree.meters["nuts"] -= 1
        basket.meters["nuts"] += 1
        hero.memes["greed"] += 0.5
        world.sound_log.append(shake_sound(world))
        world.say(
            f"{hero.name_or_label()} made the same choice again: {choice.repeated_action}. {shake_sound(world).capitalize()}!"
        )
        if world.repeated_count == 1:
            world.say("The first nut dropped cleanly.")
        else:
            world.say(choice.turn + ".")
        hero.meters["trouble"] += 1
        world.say(f"By then, {choice.trouble}.")
    world.para()

    hero.memes["patience"] += 1
    world.say(
        f"At last, {hero.name_or_label()} stopped and listened to the little rustle in the leaves."
    )
    world.say(
        f"{hero.name_or_label()} chose to {choice.final_action}. {turn_sound(world).capitalize()}!"
    )
    world.say(
        f"That quiet choice changed the day: {choice.resolution}."
    )
    hero.memes["kindness"] += 1
    hero.meters["calm"] += 1
    world.fixed = True

    world.facts.update(
        hero=hero,
        tree=tree,
        basket=basket,
        choice=choice,
        repeated_count=world.repeated_count,
        fixed=world.fixed,
        lesson=choice.lesson,
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.hero
    return [
        f'Write a short fable about {hero.label} under a hickory tree, with a repeated action and a small sound effect.',
        f'Tell a child-friendly story where {hero.name_or_label()} repeats the same mistake near hickory nuts, then learns a lesson.',
        f'Write a gentle fable that includes the word "hickory" and ends with a wiser choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.hero
    choice = world.choice
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.label}, who lives near a hickory tree.",
        ),
        QAItem(
            question=f"What did {hero.name_or_label()} keep doing again and again?",
            answer=f"{hero.name_or_label()} kept {choice.repeated_action}. That repetition made the trouble grow.",
        ),
        QAItem(
            question=f"What sound effect was heard when the action repeated?",
            answer=f"The story used the sound effect \"{shake_sound(world)}\" when {hero.name_or_label()} repeated the action.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"At the end, {hero.name_or_label()} chose to {choice.final_action}, and that made the ending calm and kind.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hickory tree?",
            answer="A hickory tree is a tree that can grow hard nuts with shells that are not easy to crack.",
        ),
        QAItem(
            question="Why do fables repeat actions?",
            answer="Fables often repeat an action so the lesson feels clear and memorable.",
        ),
        QAItem(
            question="Why do stories use sound effects?",
            answer="Sound effects help a reader hear the action in their mind and make the story feel lively.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
% A fable is reasonable when the hero repeats a choice near hickory nuts,
% then changes to a gentler or wiser ending.
hero(squirrel;crow;rabbit).
lesson(share;listen;patient).
repeatable(squirrel, snatch_nuts).
repeatable(crow, peck_shell).
repeatable(rabbit, hop_back).

has_end(squirrel, share).
has_end(crow, listen).
has_end(rabbit, patient).

valid(H, L) :- hero(H), lesson(L), has_end(H, L).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("tree", "hickory"),
        asp.fact("sound_theme", "repetition"),
        asp.fact("sound_theme", "sound_effects"),
    ]
    for h in HEROES:
        lines.append(asp.fact("hero", h))
    for l in LESSONS:
        lines.append(asp.fact("lesson", l))
    for c in CHOICES.values():
        lines.append(asp.fact("has_end", c.hero, c.lesson))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str]]:
    return sorted((c.hero, c.lesson) for c in CHOICES.values())


def asp_verify() -> int:
    a = set(asp_valid())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in [world.hero, world.tree, world.basket]:
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  repeated_count={world.repeated_count}")
    lines.append(f"  fixed={world.fixed}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable storyworld with hickory, repetition, and sound effects.")
    ap.add_argument("--hero", choices=sorted(HEROES))
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.hero:
        combos = [c for c in combos if c[0] == args.hero]
    if args.lesson:
        combos = [c for c in combos if c[1] == args.lesson]
    if not combos:
        raise StoryError("No valid fable matches the requested options.")
    hero, lesson = rng.choice(combos)
    return StoryParams(hero=hero, lesson=lesson)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
    StoryParams(hero="squirrel", lesson="share"),
    StoryParams(hero="crow", lesson="listen"),
    StoryParams(hero="rabbit", lesson="be patient"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} compatible (hero, lesson) combos:")
        for hero, lesson in vals:
            print(f"  {hero:8} {lesson}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} / {p.lesson}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
