#!/usr/bin/env python3
"""A tiny superhero storyworld about bacon, removal, a twist, and reconciliation."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Hero:
    name: str
    title: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class Conflict:
    bacon: str
    remove: str
    twist: str
    reconciliation: str
    resolved: bool = False


@dataclass
class StoryParams:
    seed: Optional[int] = None
    setting: str = "sunlit city block"
    hero_name: str = "Captain Crisp"
    sidekick_name: str = "Mira"
    villain_name: str = "The Grease Ghost"
    bacon_item: str = "bacon"
    remove_item: str = "remove"
    twist: str = "the bacon was only a smoky signal, not the real problem"
    reconciliation: str = "the hero and the misunderstood villain shared the last sandwich and fixed the mix-up"


@dataclass
class World:
    place: Place
    hero: Hero
    sidekick: Hero
    villain: Hero
    conflict: Conflict
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


HEROES = [
    ("Captain Crisp", "hero"),
    ("Star Lantern", "hero"),
    ("Blue Comet", "hero"),
    ("Mira", "sidekick"),
    ("Nova Byte", "sidekick"),
]
VILLAINS = [
    ("The Grease Ghost", "villain"),
    ("Professor Twist", "villain"),
    ("Lady Echo", "villain"),
]
SETTINGS = [
    "sunlit city block",
    "rooftop garden",
    "small subway station",
    "busy boardwalk",
]
TWISTS = [
    "the bacon was only a smoky signal, not the real problem",
    "the missing bacon had been hiding inside a lunch box all along",
    "the strange trail of bacon led to a broken vent fan",
    "everyone had blamed the wrong mask for the trouble",
]
RECONCILIATIONS = [
    "the hero and the misunderstood villain shared the last sandwich and fixed the mix-up",
    "the city team apologized, and the villain helped clean the kitchen",
    "the neighbors laughed, then worked together to rebuild the snack cart",
    "the rival heroes shook hands and agreed to split the breakfast patrol",
]


ASP_RULES = r"""
hero(X) :- hero_name(X).
conflict(C) :- bacon(C), remove(C), twist(C), reconciliation(C).
resolved(C) :- conflict(C), twist(C), reconciliation(C).
good_end(X) :- hero(X), resolved(conflict).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("hero_name", "Captain Crisp")]
    lines.append(asp.fact("bacon", "conflict"))
    lines.append(asp.fact("remove", "conflict"))
    lines.append(asp.fact("twist", "conflict"))
    lines.append(asp.fact("reconciliation", "conflict"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/1."))
    asp_resolved = set(asp.atoms(model, "resolved"))
    py_resolved = {("conflict",)}
    if asp_resolved == py_resolved:
        print("OK: clingo gate matches python reasoning (1 conflict).")
        return 0
    print("MISMATCH between clingo and python reasoning.")
    print("clingo:", sorted(asp_resolved))
    print("python:", sorted(py_resolved))
    return 1


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(str(value) for value in (
        params.seed, params.setting, params.hero_name, params.sidekick_name,
        params.villain_name, params.bacon_item, params.remove_item,
        params.twist, params.reconciliation,
    ))
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def build_world(params: StoryParams) -> World:
    if not params.setting:
        raise StoryError("setting must not be empty")
    return World(
        place=Place(name=params.setting, kind="city"),
        hero=Hero(name=params.hero_name, title="hero"),
        sidekick=Hero(name=params.sidekick_name, title="sidekick"),
        villain=Hero(name=params.villain_name, title="villain"),
        conflict=Conflict(
            bacon=params.bacon_item,
            remove=params.remove_item,
            twist=params.twist,
            reconciliation=params.reconciliation,
        ),
    )


def tell_story(world: World, params: StoryParams) -> None:
    rng = story_rng(params)
    h, s, v, place, c = world.hero, world.sidekick, world.villain, world.place, world.conflict
    h.memes.update(courage=2, worry=1)
    s.memes.update(curiosity=2)
    v.memes.update(misunderstood=1)

    world.say(
        f"On a bright day in {place.name}, {h.name} was on patrol when a trail of {c.bacon} shimmered along the sidewalk."
    )
    world.say(
        f'"We should {c.remove} the mess," {s.name} said. "{h.name}, do you think it points to trouble?"'
    )
    world.say(
        f'"Yes," {h.name} said, and pointed up at the broken sign. "Stay close. We will check every clue before we jump."' 
    )

    world.para()
    world.say(
        f"They followed the shiny trail to a rooftop kitchen, where {v.name} stood beside a smoky pan and a wobbling snack cart."
    )
    world.say(
        f'"You think I stole the {c.bacon}," {v.name} said, "but I was trying to stop the grill from sparking."'
    )
    world.say(
        f'{s.name} blinked. "{c.remove} the smoke could have hidden the real danger?"'
    )

    world.para()
    world.say(
        f"Then came the twist: {c.twist}. The cracked vent had blown smoke into the alley, and the bacon smell had sent everyone the wrong way."
    )
    world.say(
        f'"So you were helping?" {h.name} asked.'
    )
    world.say(
        f'"I was," {v.name} answered, lowering the pan. "I only wanted the family lunch to stay safe."'
    )

    world.para()
    world.say(
        f"{h.name} nodded. Instead of chasing a fight, the heroes chose reconciliation: {c.reconciliation}."
    )
    world.say(
        f'"Let us fix the vent together," {h.name} said. "{v.name}, you keep the grill cool. {s.name}, hand me the wrench."'
    )
    world.say(
        f'By sunset, the smell of bacon drifted from a repaired kitchen, and {v.name} smiled beside the shining cart while the city cheered.'
    )

    c.resolved = True
    world.facts.update(hero=h, sidekick=s, villain=v, place=place, conflict=c)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly superhero story in {f['place'].name} where {f['hero'].name} investigates bacon and learns when to remove a false alarm.",
        f"Tell a short superhero tale with a twist and reconciliation, ending with the city safe again.",
        f"Use clear dialogue, a surprise twist, and a friendly ending about {f['villain'].name} helping instead of fighting.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c = f["conflict"]
    return [
        QAItem(
            question=f"What clue did {f['hero'].name} find at the start?",
            answer=f"{f['hero'].name} found a trail of {c.bacon} in {f['place'].name}."),
        QAItem(
            question=f"What did {f['sidekick'].name} want to do with the mess?",
            answer=f"{f['sidekick'].name} wanted to {c.remove} the mess and look for the real problem."),
        QAItem(
            question="What was the twist in the story?",
            answer=c.twist.capitalize() + "."),
        QAItem(
            question=f"How did {f['hero'].name} and {f['villain'].name} resolve the conflict?",
            answer=f"They chose reconciliation: {c.reconciliation}."),
        QAItem(
            question="How did the story end?",
            answer="The kitchen was repaired, the misunderstanding was cleared up, and the city ended in a calm, cheerful mood."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes the true situation different from what characters first believed."),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who misunderstood each other make peace and work together again."),
        QAItem(
            question="Can a superhero story end with cooperation instead of a fight?",
            answer="Yes. A superhero story can end with teamwork, apology, and a safer solution."),
        QAItem(
            question="Why are spoken lines important here?",
            answer="The dialogue lets the characters change what they know and decide what to do next."),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny superhero storyworld with bacon, removal, twist, and reconciliation.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero_name, _ = rng.choice(HEROES[:3])
    sidekick_name, _ = rng.choice(HEROES[3:5])
    villain_name, _ = rng.choice(VILLAINS)
    return StoryParams(
        seed=args.seed,
        setting=rng.choice(SETTINGS),
        hero_name=hero_name,
        sidekick_name=sidekick_name,
        villain_name=villain_name,
        bacon_item="bacon",
        remove_item="remove",
        twist=rng.choice(TWISTS),
        reconciliation=rng.choice(RECONCILIATIONS),
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in (world.place, world.hero, world.sidekick, world.villain):
        lines.append(f"{entity.name}: meters={entity.meters} memes={entity.memes}")
    lines.append(
        f"conflict: bacon={world.conflict.bacon!r} remove={world.conflict.remove!r} "
        f"twist={world.conflict.twist!r} reconciliation={world.conflict.reconciliation!r} "
        f"resolved={world.conflict.resolved}"
    )
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n== prompts ==")
        for i, prompt in enumerate(sample.prompts, 1):
            print(f"{i}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/1."))
        print(sorted(set(asp.atoms(model, "resolved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = 3 if args.all else args.n
    samples: list[StorySample] = []
    for i in range(count):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([asdict(s.params) | {"story": s.story, "prompts": s.prompts, "story_qa": [asdict(q) for q in s.story_qa], "world_qa": [asdict(q) for q in s.world_qa]} for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
