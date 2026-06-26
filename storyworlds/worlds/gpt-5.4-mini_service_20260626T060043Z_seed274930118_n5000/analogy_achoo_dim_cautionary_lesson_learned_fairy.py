#!/usr/bin/env python3
"""
A tiny fairy-tale storyworld about an analogy, an achoo-dim sneeze, and a
cautionary lesson learned.

The seed tale that shaped this world:
- A small fairy-tale character ignores a warning.
- A strange dim dust or pollen makes them sneeze "achoo".
- A careful helper explains the situation with an analogy.
- The hero learns a lesson and avoids trouble next time.

This world generates short, child-facing cautionary tales with a clear turn:
curiosity, warning, small mishap, analogy, and a lesson learned.
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


@dataclass
class Character:
    name: str
    role: str
    kind: str = "character"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "they"

    def possessive(self) -> str:
        return "their"


@dataclass
class Object:
    name: str
    kind: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    feature: str
    dimness: str
    wind: str


@dataclass
class StoryParams:
    place: str
    feature: str
    name: str
    helper: str
    lesson: str
    seed: Optional[int] = None


SETTINGS = {
    "mossy_lane": Setting(place="the mossy lane", feature="a dim lantern glow", dimness="dim", wind="soft"),
    "old_wood": Setting(place="the old wood", feature="a hush of leaf-shadow", dimness="dim", wind="whispery"),
    "brook_path": Setting(place="the brook path", feature="sparkling reeds", dimness="soft", wind="cool"),
    "fairy_glen": Setting(place="the fairy glen", feature="tiny mushrooms", dimness="gentle", wind="merry"),
}

NAMES = ["Mina", "Tilda", "Poppy", "Nell", "Lark", "Clover", "Ivy", "Rosie"]
HELPERS = ["a wise fox", "a kind squirrel", "an old owl", "a gentle mouse"]
LESSONS = [
    "to listen before touching strange dust",
    "to ask first when something looks tricky",
    "to keep away from sleepy lantern soot",
    "to stay careful when the air feels dim and prickly",
]

ASP_RULES = r"""
kind(place).
feature(place,dimness).
feature(place,wind).
lesson_choice(lessons).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for key, s in SETTINGS.items():
        lines.append(asp.fact("place", key))
        lines.append(asp.fact("setting_place", key, s.place))
        lines.append(asp.fact("feature_of", key, s.feature))
        lines.append(asp.fact("dimness_of", key, s.dimness))
        lines.append(asp.fact("wind_of", key, s.wind))
    for n in NAMES:
        lines.append(asp.fact("name", n))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld with analogy and an achoo-dim lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
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
    place = args.place or rng.choice(list(SETTINGS))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    lesson = args.lesson or rng.choice(LESSONS)
    return StoryParams(place=place, feature=SETTINGS[place].feature, name=name, helper=helper, lesson=lesson)


@dataclass
class World:
    setting: Setting
    hero: Character
    helper: Character
    soot: Object
    facts: dict = field(default_factory=dict)
    traces: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        self.traces.append(text)

    def render(self) -> str:
        return "\n\n".join(self.traces)


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    hero = Character(name=params.name, role="hero")
    helper = Character(name=params.helper, role="helper")
    soot = Object(name="dim soot")
    world = World(setting=setting, hero=hero, helper=helper, soot=soot)

    world.say(
        f"Once in {setting.place}, {hero.name} wandered near {setting.feature}, while the wind stayed {setting.wind}."
    )
    world.say(
        f"{hero.name} spotted a little puff of {soot.name} on a stone and leaned closer, curious as a kitten."
    )
    world.say(
        f"The air turned prickly, and {hero.name} gave an achoo-dim sneeze that shook the nearby fern."
    )
    world.say(
        f"{helper} stepped out and said, 'That dusty puff is like a nettle hidden in a cake: it looks small, but it can sting if you nibble too fast.'"
    )
    world.say(
        f"{hero.name} blinked, listened at last, and took a step back from the soot."
    )
    world.say(
        f"So {hero.name} learned {params.lesson}, and from then on {hero.name} bowed to strange things before touching them."
    )

    world.facts.update(
        setting=setting,
        hero=hero,
        helper=helper,
        soot=soot,
        lesson=params.lesson,
        analogy="nettles hidden in a cake",
        cautionary=True,
        learned=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fairy tale about {f["hero"].name} at {f["setting"].place} with an "achoo-dim" sneeze and a kind warning.',
        f"Tell a cautionary lesson-learned story where a helper uses an analogy to explain why {f['hero'].name} should keep away from strange dim soot.",
        f"Write a child-friendly fairy tale with the word analogy, a sneeze, and a lesson learned at {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {f['hero'].name}, who wandered through {f['setting'].place} and learned to be careful.",
        ),
        QAItem(
            question=f"What made {f['hero'].name} sneeze?",
            answer=f"A little puff of dim soot made {f['hero'].name} give an achoo-dim sneeze.",
        ),
        QAItem(
            question=f"What did the helper use to explain the danger?",
            answer=f"The helper used an analogy, comparing the dusty puff to nettles hidden in a cake.",
        ),
        QAItem(
            question=f"What lesson did {f['hero'].name} learn?",
            answer=f"{f['hero'].name} learned {f['lesson']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an analogy?",
            answer="An analogy is a comparison that helps explain something by showing how it is like something else.",
        ),
        QAItem(
            question="What does achoo mean?",
            answer="Achoo is the sound people make when they sneeze.",
        ),
        QAItem(
            question="Why should a child be careful around strange dust?",
            answer="Strange dust can be irritating or messy, so it is safer to stop and ask before touching it.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"setting: {world.setting.place}")
    lines.append(f"feature: {world.setting.feature}")
    lines.append(f"hero: {world.hero.name}")
    lines.append(f"helper: {world.helper.name}")
    lines.append(f"lesson: {world.facts.get('lesson')}")
    lines.append(f"analogy: {world.facts.get('analogy')}")
    lines.append(f"cautionary: {world.facts.get('cautionary')}")
    lines.append(f"learned: {world.facts.get('learned')}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_verify() -> int:
    import asp
    facts = asp_facts()
    if "place(" in facts and "helper(" in facts:
        print("OK: ASP facts emitted.")
        return 0
    print("MISMATCH: ASP facts missing.")
    return 1


CURATED = [
    StoryParams(place="mossy_lane", feature=SETTINGS["mossy_lane"].feature, name="Mina", helper="a wise fox", lesson=LESSONS[0]),
    StoryParams(place="old_wood", feature=SETTINGS["old_wood"].feature, name="Clover", helper="an old owl", lesson=LESSONS[1]),
    StoryParams(place="fairy_glen", feature=SETTINGS["fairy_glen"].feature, name="Nell", helper="a kind squirrel", lesson=LESSONS[2]),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show place/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(asp_program("#show place/1."))
        model = asp.one_model(asp_program("#show place/1."))
        print(sorted(set(asp.atoms(model, "place"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
