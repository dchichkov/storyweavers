#!/usr/bin/env python3
"""
A standalone story world for a tiny superhero tale with a present, a breather,
and a twist.

Premise:
- A small hero is excited about a wrapped present.
- A tricky rescue leaves them winded, so they take a breather.
- The present turns out to be part of a twist: it helps them solve the problem.

The world is modeled with physical meters and emotional memes so the prose is
driven by state changes instead of a frozen template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

@dataclass
class Person:
    id: str
    type: str = "child"
    role: str = "hero"
    label: str = ""
    pronoun_subject: str = "they"
    pronoun_object: str = "them"
    pronoun_possessive: str = "their"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def sub(self) -> str:
        return self.pronoun_subject

    def obj(self) -> str:
        return self.pronoun_object

    def pos(self) -> str:
        return self.pronoun_possessive


@dataclass
class Item:
    id: str
    label: str
    kind: str = "thing"
    owner: Optional[str] = None
    held_by: Optional[str] = None
    opened: bool = False
    useful: bool = False
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "the city square"
    vibe: str = "bright"


@dataclass
class StoryParams:
    hero: str
    sidekick: str
    villain: str
    present: str
    setting: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "city": Setting(place="the city square", vibe="bright"),
    "roof": Setting(place="the rooftop", vibe="windy"),
    "train": Setting(place="the train station", vibe="busy"),
}

HEROES = [
    ("Nova", "she", "her", "her"),
    ("Jet", "he", "him", "his"),
    ("Sky", "they", "them", "their"),
]

SIDEKICKS = [
    ("Pip", "they", "them", "their"),
    ("Milo", "he", "him", "his"),
    ("Luna", "she", "her", "her"),
]

VILLAINS = [
    "Grim Mask",
    "Captain Clatter",
    "Shadow Bolt",
]

PRESENTS = {
    "box": "a red present with a silver ribbon",
    "capsule": "a tiny present wrapped in blue paper",
    "parcel": "a shiny present with a star sticker",
}

# What the present really is for
PRESENT_TWISTS = {
    "box": ("signal key", "key"),
    "capsule": ("mini rescue beacon", "beacon"),
    "parcel": ("map piece", "map"),
}

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero(H) :- hero_name(H).
sidekick(S) :- sidekick_name(S).
villain(V) :- villain_name(V).
setting(Place) :- setting_name(Place).
present(P) :- present_name(P).

needs_breather(H) :- tired(H), after_rescue(H).
twist(H) :- opens_present(H,P), useful_present(P).
resolved(H) :- twist(H), uses_help(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for h, *_ in HEROES:
        lines.append(asp.fact("hero_name", h))
    for s, *_ in SIDEKICKS:
        lines.append(asp.fact("sidekick_name", s))
    for v in VILLAINS:
        lines.append(asp.fact("villain_name", v))
    for s in SETTINGS:
        lines.append(asp.fact("setting_name", s))
    for p in PRESENTS:
        lines.append(asp.fact("present_name", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show hero/1."))
    if asp.atoms(model, "hero") == [("Nova",), ("Jet",), ("Sky",)]:
        print("OK: ASP twin loads and produces expected registry facts.")
        return 0
    print("ASP verification failed.")
    return 1


# ---------------------------------------------------------------------------
# Helper logic
# ---------------------------------------------------------------------------

def pick(rng: random.Random, seq):
    return rng.choice(list(seq))


def hero_phrase(hero: Person) -> str:
    return f"{hero.label}" if hero.label else hero.id


def setting_sentence(world: World) -> str:
    if world.setting.vibe == "windy":
        return f"The wind rushed across {world.setting.place}, making every cape flutter."
    if world.setting.vibe == "busy":
        return f"{world.setting.place} buzzed with people and flashing lights."
    return f"{world.setting.place} glowed in the afternoon sun."


def run_rescue(world: World) -> None:
    hero: Person = world.get("hero")
    sidekick: Person = world.get("sidekick")
    villain = world.get("villain")
    rescue_item: Item = world.get("present")

    hero.meters["tired"] = 1.0
    hero.memes["hope"] = 1.0
    hero.memes["worry"] = 1.0
    world.say(
        f"{hero_phrase(hero)} sprinted into {world.setting.place} to stop {villain.label}, "
        f"and {hero.sub()} had to carry a wobbling bundle at the same time."
    )
    world.say(
        f"{sidekick.label} called out, '{hero_phrase(hero)}, take a breather!' "
        f"so {hero.sub()} slowed down and gulped a few deep breaths."
    )
    hero.meters["breather"] = 1.0
    hero.memes["calm"] = 1.0
    world.say(
        f"For a moment, {hero.sub()} stood still and listened to the city sounds. "
        f"That breather helped {hero.obj()} think."
    )

    rescue_item.opened = True
    hero.memes["curious"] = 1.0
    world.say(
        f"Then {hero.sub()} opened the present and found {rescue_item.label} inside."
    )

    # Twist: the gift is actually the missing tool.
    rescue_item.useful = True
    world.facts["twist"] = True
    world.facts["tool"] = PRESENT_TWISTS[rescue_item.kind][0]
    world.say(
        f"The twist was that the present was not a toy at all. It was a "
        f"{PRESENT_TWISTS[rescue_item.kind][0]} that could shut down {villain.label}'s trick."
    )

    hero.memes["joy"] = 1.0
    hero.memes["brave"] = 1.0
    world.say(
        f"{hero_phrase(hero)} used it right away, and the dark machine clicked off. "
        f"With the villain stunned, the crowd cheered."
    )
    world.say(
        f"{hero.sub().capitalize()} smiled, hugged {sidekick.label}, and held the open present high. "
        f"It had started as a mystery, but it ended as the thing that saved the day."
    )
    world.facts["resolved"] = True


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_story(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)

    hero_name, hsub, hobj, hpos = next((h for h in HEROES if h[0] == params.hero), HEROES[0])
    side_name, ssub, sobj, spos = next((s for s in SIDEKICKS if s[0] == params.sidekick), SIDEKICKS[0])

    hero = world.add(Person(
        id="hero",
        type="child",
        role="hero",
        label=hero_name,
        pronoun_subject=hsub,
        pronoun_object=hobj,
        pronoun_possessive=hpos,
    ))
    sidekick = world.add(Person(
        id="sidekick",
        type="child",
        role="sidekick",
        label=side_name,
        pronoun_subject=ssub,
        pronoun_object=sobj,
        pronoun_possessive=spos,
    ))
    villain = world.add(Person(
        id="villain",
        type="villain",
        role="villain",
        label=params.villain,
        pronoun_subject="he",
        pronoun_object="him",
        pronoun_possessive="his",
    ))
    present = world.add(Item(
        id="present",
        label=PRESENTS[params.present],
        kind=params.present,
        owner=hero.id,
    ))

    world.say(
        f"{hero.label} was a small superhero who never liked leaving a mystery alone."
    )
    world.say(
        f"{hero.label} had a present from {sidekick.label}, and the ribbon made {hero.pos()} fingers itch with curiosity."
    )
    world.say(setting_sentence(world))

    world.para()
    run_rescue(world)

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        villain=villain,
        present=present,
        setting=params.setting,
    )
    return world


def make_story(params: StoryParams) -> StorySample:
    world = build_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    h: Person = world.facts["hero"]
    s: Person = world.facts["sidekick"]
    v: Person = world.facts["villain"]
    p: Item = world.facts["present"]
    return [
        f"Write a short superhero story for little kids about {h.label}, {s.label}, and a present with a twist.",
        f"Tell a child-friendly adventure where {h.label} must take a breather before using a present to stop {v.label}.",
        f"Write a simple superhero tale that includes the words present and breather and ends with a helpful twist.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h: Person = world.facts["hero"]
    s: Person = world.facts["sidekick"]
    v: Person = world.facts["villain"]
    p: Item = world.facts["present"]
    tool = world.facts.get("tool", "tool")

    return [
        QAItem(
            question=f"Why did {h.label} take a breather?",
            answer=f"{h.label} was tired from rushing into {world.setting.place}, so {h.label} stopped to take a breather and think more clearly.",
        ),
        QAItem(
            question=f"What was the twist about the present?",
            answer=f"The twist was that the present was useful, not just fun. It held a {tool} that helped stop {v.label}'s trick.",
        ),
        QAItem(
            question=f"Who helped {h.label} before the present was opened?",
            answer=f"{s.label} helped by telling {h.label} to take a breather and slow down.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a breather?",
            answer="A breather is a short pause to rest and calm down before doing something hard again.",
        ),
        QAItem(
            question="What is a present?",
            answer="A present is a gift that someone gives to another person, often wrapped in paper or a box.",
        ),
        QAItem(
            question="What does a superhero do?",
            answer="A superhero helps people, solves problems, and uses courage to protect others.",
        ),
    ]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny superhero storyworld with a present, a breather, and a twist.")
    ap.add_argument("--hero", choices=[h[0] for h in HEROES])
    ap.add_argument("--sidekick", choices=[s[0] for s in SIDEKICKS])
    ap.add_argument("--villain", choices=VILLAINS)
    ap.add_argument("--present", choices=PRESENTS)
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
    hero = args.hero or pick(rng, [h[0] for h in HEROES])
    sidekick = args.sidekick or pick(rng, [s[0] for s in SIDEKICKS])
    villain = args.villain or pick(rng, VILLAINS)
    present = args.present or pick(rng, list(PRESENTS))
    setting = args.setting or pick(rng, list(SETTINGS))
    return StoryParams(hero=hero, sidekick=sidekick, villain=villain, present=present, setting=setting)


def generate(params: StoryParams) -> StorySample:
    return make_story(params)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        if isinstance(e, Person):
            lines.append(
                f"{e.id}: label={e.label}, meters={dict(e.meters)}, memes={dict(e.memes)}"
            )
        else:
            lines.append(
                f"{e.id}: label={e.label}, opened={e.opened}, useful={e.useful}"
            )
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


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
        print(asp_program("#show hero/1. #show sidekick/1. #show villain/1. #show present/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show hero/1. #show sidekick/1. #show villain/1. #show present/1."))
        print(json.dumps({
            "hero": asp.atoms(model, "hero"),
            "sidekick": asp.atoms(model, "sidekick"),
            "villain": asp.atoms(model, "villain"),
            "present": asp.atoms(model, "present"),
        }, indent=2))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Nova", "Pip", "Shadow Bolt", "box", "city"),
            StoryParams("Jet", "Luna", "Captain Clatter", "capsule", "roof"),
            StoryParams("Sky", "Milo", "Grim Mask", "parcel", "train"),
        ]
        samples = [generate(p) for p in curated]
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
